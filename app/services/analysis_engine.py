from datetime import datetime, timezone

from app.services.market_data import (
    get_klines,
    compute_rsi,
    compute_macd,
    compute_support_resistance,
)


async def analyze(symbol: str):
    symbol = symbol.upper().strip().replace("/USDT", "").replace("USDT", "")
    if not symbol:
        raise ValueError("Merci d'indiquer une crypto (ex: BTC, ETH, SOL...).")

    try:
        klines = await get_klines(symbol, interval="1h", limit=100)
    except Exception:
        raise ValueError(
            f"Impossible de récupérer les données pour {symbol}. "
            "Vérifiez que ce symbole existe sur Binance (ex: BTC, ETH, SOL...)."
        )

    if not klines:
        raise ValueError(f"Aucune donnée trouvée pour {symbol}.")

    closes = [k["close"] for k in klines]
    price = closes[-1]
    rsi = compute_rsi(closes)
    macd_line, macd_signal, macd_hist = compute_macd(closes)
    support, resistance = compute_support_resistance(klines)

    if rsi is None or macd_line is None:
        trend, signal, confidence = "neutre", "ATTENDRE", 50
    else:
        bullish = rsi >= 55 and macd_hist > 0
        bearish = rsi <= 45 and macd_hist < 0
        trend = "haussière" if bullish else "baissière" if bearish else "neutre"
        signal = "ACHAT" if trend == "haussière" else "VENTE" if trend == "baissière" else "ATTENDRE"
        confidence = min(96, max(50, int(60 + abs(rsi - 50) * 0.8 + abs(macd_hist) * 2)))

    return {
        "symbol": symbol,
        "pair": f"{symbol}/USDT",
        "price": round(price, 6),
        "rsi": rsi,
        "macd": macd_line,
        "macd_signal": macd_signal,
        "macd_hist": macd_hist,
        "trend": trend,
        "signal": signal,
        "confidence": confidence,
        "support": support,
        "resistance": resistance,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
