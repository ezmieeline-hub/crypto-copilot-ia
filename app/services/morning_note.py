"""
Morning Note Engine — Skill GitHub Anthropic adapté Crypto
Intègre : Binance (prix, orderbook, funding), macro crypto (BTC dominance, Fear & Greed),
actualités multi-sources, et génère une note matinale actionnable.
"""

import os
import httpx
from datetime import datetime, timezone
from typing import Any

from app.services.market_data import get_klines, compute_rsi, compute_volatility
from app.services.news_service import get_crypto_news

# ============================================================
# CONFIG
# ============================================================

FEAR_GREED_URL = "https://api.alternative.me/fng/?limit=1"
BTC_DOMINANCE_URL = "https://api.coingecko.com/api/v3/global"
BINANCE_FUNDING_URL = "https://fapi.binance.com/fapi/v1/fundingRate"
BINANCE_ORDERBOOK_URL = "https://api.binance.com/api/v3/depth"

# ============================================================
# HELPERS
# ============================================================

def utc_now():
    return datetime.now(timezone.utc).isoformat()

def safe_float(v):
    try:
        return float(v) if v is not None else None
    except:
        return None

# ============================================================
# MACRO DATA FETCHERS
# ============================================================

async def get_fear_greed_index() -> dict:
    """Récupère le Fear & Greed Index crypto."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(FEAR_GREED_URL)
            r.raise_for_status()
            data = r.json()
            item = data["data"][0]
            return {
                "value": int(item["value"]),
                "classification": item["value_classification"],
                "timestamp": item["timestamp"],
            }
    except Exception:
        return None

async def get_btc_dominance() -> float:
    """Récupère la dominance du BTC via CoinGecko."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(BTC_DOMINANCE_URL)
            r.raise_for_status()
            data = r.json()
            return safe_float(data["data"]["market_cap_percentage"]["btc"])
    except Exception:
        return None

async def get_funding_rate(symbol: str) -> dict:
    """Récupère le funding rate perpetual Binance."""
    pair = symbol.upper().strip().replace("/", "").replace("USDT", "") + "USDT"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(
                BINANCE_FUNDING_URL,
                params={"symbol": pair, "limit": 1},
            )
            r.raise_for_status()
            data = r.json()
            if data:
                return {
                    "rate": safe_float(data[0]["fundingRate"]),
                    "time": data[0]["fundingTime"],
                }
    except Exception:
        pass
    return None

async def get_orderbook_snapshot(symbol: str, limit: int = 100) -> dict:
    """Récupère un snapshot du carnet d'ordres pour calculer le ratio bid/ask."""
    pair = symbol.upper().strip().replace("/", "").replace("USDT", "") + "USDT"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(
                BINANCE_ORDERBOOK_URL,
                params={"symbol": pair, "limit": limit},
            )
            r.raise_for_status()
            data = r.json()
            bids = data.get("bids", [])
            asks = data.get("asks", [])
            bid_vol = sum(float(b[1]) for b in bids)
            ask_vol = sum(float(a[1]) for a in asks)
            total = bid_vol + ask_vol
            return {
                "bid_volume": round(bid_vol, 4),
                "ask_volume": round(ask_vol, 4),
                "bid_ask_ratio": round(bid_vol / ask_vol, 2) if ask_vol else None,
                "bid_ask_imbalance_pct": round((bid_vol - ask_vol) / total * 100, 2) if total else None,
                "spread_pct": round((float(asks[0][0]) - float(bids[0][0])) / float(bids[0][0]) * 100, 4) if bids and asks else None,
            }
    except Exception:
        return None

# ============================================================
# MARKET CONTEXT BUILDER
# ============================================================

async def build_macro_context(symbol: str) -> dict:
    """Agrège toutes les données macro et de marché pour le morning note."""
    ctx = {
        "generated_at": utc_now(),
        "symbol": symbol.upper(),
    }

    # Fear & Greed
    ctx["fear_greed"] = await get_fear_greed_index()

    # BTC Dominance
    ctx["btc_dominance"] = await get_btc_dominance()

    # Funding Rate
    ctx["funding_rate"] = await get_funding_rate(symbol)

    # Order Book
    ctx["orderbook"] = await get_orderbook_snapshot(symbol)

    # Klines pour RSI et volatilité overnight
    try:
        klines = await get_klines(symbol, interval="1h", limit=50)
        closes = [k["close"] for k in klines]
        ctx["rsi_1h"] = compute_rsi(closes)
        ctx["volatility_1h"] = compute_volatility(closes)
        ctx["price_now"] = closes[-1] if closes else None
        ctx["price_24h_ago"] = closes[-24] if len(closes) >= 24 else None
        if ctx["price_now"] and ctx["price_24h_ago"]:
            ctx["change_24h_pct"] = round(
                (ctx["price_now"] - ctx["price_24h_ago"]) / ctx["price_24h_ago"] * 100, 2
            )
    except Exception:
        ctx["rsi_1h"] = None
        ctx["volatility_1h"] = None
        ctx["price_now"] = None
        ctx["change_24h_pct"] = None

    # News
    ctx["news"] = await get_crypto_news(
        symbol, os.environ.get("CRYPTOPANIC_API_KEY", ""), limit=5
    )

    return ctx

# ============================================================
# MORNING NOTE GENERATOR
# ============================================================

def _sentiment_from_fear_greed(fg: dict) -> str:
    if not fg:
        return "Inconnu"
    val = fg["value"]
    if val >= 75:
        return "Extrême cupidité 🟢"
    if val >= 55:
        return "Cupidité 🟡"
    if val >= 45:
        return "Neutre ⚪"
    if val >= 25:
        return "Peur 🟠"
    return "Extrême peur 🔴"

def _funding_sentiment(rate: float) -> str:
    if rate is None:
        return "Inconnu"
    if rate > 0.01:
        return "Très haussier (longs payent) 🔴"
    if rate > 0.001:
        return "Légèrement haussier 🟠"
    if rate < -0.01:
        return "Très baissier (shorts payent) 🟢"
    if rate < -0.001:
        return "Légèrement baissier 🟡"
    return "Neutre ⚪"

def _orderbook_sentiment(ob: dict) -> str:
    if not ob or ob.get("bid_ask_ratio") is None:
        return "Inconnu"
    ratio = ob["bid_ask_ratio"]
    imb = ob.get("bid_ask_imbalance_pct", 0)
    if ratio > 1.5 and imb > 10:
        return "Fort déséquilibre acheteur 🟢"
    if ratio < 0.7 and imb < -10:
        return "Fort déséquilibre vendeur 🔴"
    if ratio > 1.2:
        return "Léger déséquilibre acheteur 🟡"
    if ratio < 0.8:
        return "Léger déséquilibre vendeur 🟠"
    return "Équilibré ⚪"

def generate_morning_note(ctx: dict) -> dict:
    """Génère la morning note structurée à partir du contexte marché."""

    symbol = ctx.get("symbol", "?")
    now = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M UTC")

    fg = ctx.get("fear_greed")
    btc_dom = ctx.get("btc_dominance")
    funding = ctx.get("funding_rate")
    ob = ctx.get("orderbook")
    news_list = ctx.get("news", [])
    price = ctx.get("price_now")
    change = ctx.get("change_24h_pct")
    rsi = ctx.get("rsi_1h")
    vol = ctx.get("volatility_1h")

    # --- TOP CALL ---
    top_call_headline = f"Analyse matinale {symbol}"
    top_call_body = []

    if change is not None:
        direction = "en hausse" if change > 0 else "en baisse" if change < 0 else "stable"
        top_call_body.append(f"{symbol} est {direction} de {abs(change)}% sur 24h.")

    if rsi is not None:
        if rsi > 70:
            top_call_body.append(f"RSI suracheté ({rsi}) — attention à un retracement.")
        elif rsi < 30:
            top_call_body.append(f"RSI survendu ({rsi}) — opportunité potentielle.")
        else:
            top_call_body.append(f"RSI neutre ({rsi}).")

    if vol is not None and vol > 5:
        top_call_body.append(f"Volatilité élevée ({vol}%) — privilégier des stops larges.")

    top_call = {
        "headline": top_call_headline,
        "body": " ".join(top_call_body) if top_call_body else "Aucun mouvement significatif détecté.",
    }

    # --- OVERNIGHT DEVELOPMENTS ---
    overnight = []

    if btc_dom is not None:
        overnight.append({
            "category": "Macro",
            "title": f"BTC Dominance : {btc_dom}%",
            "take": "Alt-season limitée" if btc_dom > 55 else "Capitalisation altcoins favorable" if btc_dom < 50 else "Équilibre BTC/Alts",
        })

    if fg is not None:
        overnight.append({
            "category": "Sentiment",
            "title": f"Fear & Greed : {fg['value']} — {fg['classification']}",
            "take": _sentiment_from_fear_greed(fg),
        })

    if funding is not None:
        overnight.append({
            "category": "Perpétuel",
            "title": f"Funding Rate : {funding['rate']*100:.4f}%",
            "take": _funding_sentiment(funding["rate"]),
        })

    if ob is not None:
        overnight.append({
            "category": "Order Book",
            "title": f"Bid/Ask ratio : {ob.get('bid_ask_ratio', 'N/A')}",
            "take": _orderbook_sentiment(ob),
        })

    # --- KEY EVENTS TODAY ---
    events = []
    if news_list:
        for n in news_list[:3]:
            events.append({
                "time": n.get("published_at", "—")[:10],
                "title": n.get("title", "—"),
                "source": n.get("source", "—"),
            })
    else:
        events.append({
            "time": now,
            "title": "Aucune actualité majeure détectée pour cette crypto.",
            "source": "Crypto Copilot",
        })

    # --- TRADE IDEAS ---
    trade_ideas = []
    if rsi is not None and ob is not None:
        ob_sentiment = _orderbook_sentiment(ob)
        if rsi < 35 and "acheteur" in ob_sentiment.lower():
            trade_ideas.append({
                "direction": "LONG",
                "symbol": symbol,
                "thesis": f"RSI survendu ({rsi}) + pression acheteuse visible sur le carnet d'ordres.",
                "catalyst": "Rebond technique sur support avec confirmation volume.",
                "risk": "Breakdown sous le support majeur ou continuation de la tendance baissière.",
            })
        elif rsi > 65 and "vendeur" in ob_sentiment.lower():
            trade_ideas.append({
                "direction": "SHORT",
                "symbol": symbol,
                "thesis": f"RSI suracheté ({rsi}) + pression vendeuse sur le carnet d'ordres.",
                "catalyst": "Retracement après extension haussière.",
                "risk": "Breakout haussier continu avec FOMO acheteur.",
            })
        else:
            trade_ideas.append({
                "direction": "ATTENDRE",
                "symbol": symbol,
                "thesis": "Conditions mixtes — pas de confluence claire pour l'instant.",
                "catalyst": "Attendre une cassure de structure ou un retest de zone clé.",
                "risk": "Entrée prématurée dans un range sans direction.",
            })

    # --- INDICATORS SUMMARY ---
    indicators = {
        "price": price,
        "change_24h_pct": change,
        "rsi_1h": rsi,
        "volatility_1h": vol,
        "btc_dominance": btc_dom,
        "fear_greed_value": fg["value"] if fg else None,
        "fear_greed_class": fg["classification"] if fg else None,
        "funding_rate": funding["rate"] * 100 if funding else None,
        "orderbook_bid_ask_ratio": ob["bid_ask_ratio"] if ob else None,
        "orderbook_imbalance_pct": ob["bid_ask_imbalance_pct"] if ob else None,
        "orderbook_spread_pct": ob["spread_pct"] if ob else None,
    }

    # --- BULL / BASE / BEAR SCORE ---
    bull_score = 0
    bear_score = 0

    if change is not None:
        bull_score += max(0, change) * 2
        bear_score += max(0, -change) * 2

    if rsi is not None:
        if rsi < 30:
            bull_score += 20
        elif rsi < 40:
            bias = 10
        elif rsi > 70:
            bear_score += 20
        elif rsi > 60:
            bear_score += 10

    if ob is not None and ob.get("bid_ask_imbalance_pct") is not None:
        imb = ob["bid_ask_imbalance_pct"]
        if imb > 15:
            bull_score += 15
        elif imb > 5:
            bull_score += 5
        elif imb < -15:
            bear_score += 15
        elif imb < -5:
            bear_score += 5

    if funding is not None and funding["rate"] is not None:
        if funding["rate"] < -0.001:
            bull_score += 10  # shorts payent = sentiment baissier excessif = possible rebond
        elif funding["rate"] > 0.001:
            bear_score += 10

    total = bull_score + bear_score + 1
    bull_pct = round(bull_score / total * 100, 1)
    bear_pct = round(bear_score / total * 100, 1)
    base_pct = round(100 - bull_pct - bear_pct, 1)

    bias = "BULL" if bull_pct > bear_pct + 15 else "BEAR" if bear_pct > bull_pct + 15 else "BASE"

    return {
        "date": now,
        "symbol": symbol,
        "top_call": top_call,
        "overnight_developments": overnight,
        "key_events_today": events,
        "trade_ideas": trade_ideas,
        "indicators": indicators,
        "bias": bias,
        "bias_scores": {
            "bull": bull_pct,
            "base": base_pct,
            "bear": bear_pct,
        },
        "raw_context": ctx,
    }


# ============================================================
# PUBLIC API
# ============================================================

async def generate_morning_note_for_symbol(symbol: str) -> dict:
    """Point d'entrée principal — génère la morning note complète pour un symbole."""
    ctx = await build_macro_context(symbol)
    return generate_morning_note(ctx)
