from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Any

from app.services.market_data import (
    get_klines,
    compute_rsi,
    compute_macd,
    compute_support_resistance,
    compute_support_distance,
    compute_resistance_distance,
    compute_ema20,
    compute_ema50,
    compute_ema100,
    compute_ema200,
    compute_atr,
    compute_adx,
    compute_relative_volume,
    compute_volatility,
    compute_momentum,
    compute_trend_strength,
    compute_market_score,
    compute_take_profits,
    compute_stop_loss,
    compute_risk_reward,
    detect_breakout,
    detect_breakdown,
    detect_pullback,
    build_market_summary,
)

from app.services.vision_analysis import (
    analyze_screenshot,
)

# ============================================================
# ANALYSIS ENGINE
# ============================================================


class AnalysisEngineError(Exception):
    pass


# ============================================================
# HELPERS
# ============================================================


def utc_now():

    return datetime.now(
        timezone.utc
    ).isoformat()


def safe_float(value):

    try:

        if value is None:
            return None

        return float(value)

    except Exception:

        return None


def safe_int(value):

    try:

        if value is None:
            return None

        return int(value)

    except Exception:

        return None


def round_price(
    value,
    digits=6,
):

    if value is None:

        return None

    return round(
        float(value),
        digits,
    )


def clamp(
    value,
    minimum,
    maximum,
):

    return max(
        minimum,
        min(
            value,
            maximum,
        ),
    )


def percentage_change(
    current,
    previous,
):

    if previous in (
        None,
        0,
    ):

        return None

    return round(

        (
            (current - previous)
            / previous
        )
        * 100,

        2,

    )


def direction_from_ema(
    ema20,
    ema50,
    ema100,
    ema200,
):

    if None in (
        ema20,
        ema50,
        ema100,
        ema200,
    ):

        return "NEUTRE"

    if (
        ema20
        > ema50
        > ema100
        > ema200
    ):

        return "HAUSSIERE"

    if (
        ema20
        < ema50
        < ema100
        < ema200
    ):

        return "BAISSIERE"

    return "NEUTRE"


def normalize_score(score):

    return clamp(
        round(score, 2),
        0,
        100,
    )


# ============================================================
# MARKET CONTEXT
# ============================================================


class MarketContext:

    def __init__(self):

        self.data = {}

    def set(
        self,
        key,
        value,
    ):

        self.data[key] = value

    def get(
        self,
        key,
        default=None,
    ):

        return self.data.get(
            key,
            default,
        )

    def export(self):

        return self.data.copy()
        # ============================================================
# BUILD MARKET CONTEXT
# ============================================================

async def build_market_context(
    symbol: str,
    interval: str = "1h",
    limit: int = 300,
) -> MarketContext:

    context = MarketContext()

    klines = await get_klines(
        symbol=symbol,
        interval=interval,
        limit=limit,
    )

    if len(klines) < 200:
        raise AnalysisEngineError(
            "Historique Binance insuffisant."
        )

    closes = [
        k["close"]
        for k in klines
    ]

    current = klines[-1]
    previous = klines[-2]

    price = current["close"]

    context.set("pair", symbol.upper())
    context.set("interval", interval)
    context.set("generated_at", utc_now())

    # =====================================================
    # PRIX
    # =====================================================

    context.set("price", price)

    context.set(
        "price_change",
        percentage_change(
            current["close"],
            previous["close"],
        ),
    )

    # =====================================================
    # RSI
    # =====================================================

    rsi = compute_rsi(closes)

    context.set("rsi", rsi)

    # =====================================================
    # MACD
    # =====================================================

    macd, signal, histogram = compute_macd(
        closes
    )

    context.set("macd", macd)
    context.set("macd_signal", signal)
    context.set("macd_hist", histogram)

    # =====================================================
    # EMA
    # =====================================================

    ema20 = compute_ema20(closes)
    ema50 = compute_ema50(closes)
    ema100 = compute_ema100(closes)
    ema200 = compute_ema200(closes)

    context.set("ema20", ema20)
    context.set("ema50", ema50)
    context.set("ema100", ema100)
    context.set("ema200", ema200)

    trend = direction_from_ema(
        ema20,
        ema50,
        ema100,
        ema200,
    )

    context.set(
        "trend",
        trend,
    )

    # =====================================================
    # VOLATILITE
    # =====================================================

    atr = compute_atr(
        klines,
    )

    adx = compute_adx(
        klines,
    )

    volatility = compute_volatility(
        closes,
    )

    momentum = compute_momentum(
        closes,
    )

    context.set("atr", atr)
    context.set("adx", adx)
    context.set(
        "volatility",
        volatility,
    )
    context.set(
        "momentum",
        momentum,
    )

    # =====================================================
    # VOLUME
    # =====================================================

    relative_volume = compute_relative_volume(
        klines,
    )

    context.set(
        "relative_volume",
        relative_volume,
    )
        # =====================================================
    # SUPPORT / RESISTANCE
    # =====================================================

    support, resistance = compute_support_resistance(
        klines
    )

    context.set(
        "support",
        support,
    )

    context.set(
        "resistance",
        resistance,
    )

    context.set(

        "support_distance",

        compute_support_distance(
            price,
            support,
        ),

    )

    context.set(

        "resistance_distance",

        compute_resistance_distance(
            price,
            resistance,
        ),

    )

    # =====================================================
    # BREAKOUTS
    # =====================================================

    context.set(

        "breakout",

        detect_breakout(
            klines,
            resistance,
        ),

    )

    context.set(

        "breakdown",

        detect_breakdown(
            klines,
            support,
        ),

    )

    context.set(

        "pullback",

        detect_pullback(
            klines,
            ema20,
        ),

    )

    # =====================================================
    # SCORES
    # =====================================================

    trend_strength = compute_trend_strength(

        rsi,

        histogram,

        adx,

    )

    market_score = compute_market_score(

        rsi,

        histogram,

        adx,

        relative_volume,

    )

    context.set(
        "trend_strength",
        trend_strength,
    )

    context.set(
        "market_score",
        market_score,
    )

    context.set(

        "market_summary",

        build_market_summary(

            trend,

            trend_strength,

            rsi,

            histogram,

            adx,

        ),

    )

    # =====================================================
    # DONNEES BRUTES
    # =====================================================

    context.set(
        "klines",
        klines,
    )

    context.set(
        "closes",
        closes,
    )

    return context
    # ============================================================
# VISION ANALYSIS
# ============================================================

async def build_vision_context(
    image_bytes: bytes,
    mime_type: str,
    market_context: MarketContext,
) -> dict:

    result = await analyze_screenshot(
        image_bytes=image_bytes,
        mime_type=mime_type,
        market_context=market_context.export(),
    )

    if not isinstance(result, dict):
        raise AnalysisEngineError(
            "Vision Analysis invalide."
        )

    return result


# ============================================================
# NORMALIZATION
# ============================================================

def normalize_vision_result(
    vision: dict,
) -> dict:

    normalized = {}

    normalized["symbol"] = vision.get(
        "symbol_detected",
        "",
    )

    normalized["timeframe"] = vision.get(
        "timeframe_detected",
        "",
    )

    normalized["trend"] = vision.get(
        "trend",
        "",
    )

    normalized["trend_strength"] = vision.get(
        "trend_strength",
        "",
    )

    normalized["signal"] = vision.get(
        "signal",
        "ATTENDRE",
    ).upper()

    normalized["confidence"] = safe_int(
        vision.get("confidence")
    ) or 0

    normalized["entry"] = safe_float(
        vision.get("entry")
    )

    normalized["stop_loss"] = safe_float(
        vision.get("stop_loss")
    )

    normalized["take_profit"] = safe_float(
        vision.get("take_profit")
    )

    normalized["support"] = safe_float(
        vision.get("support")
    )

    normalized["resistance"] = safe_float(
        vision.get("resistance")
    )

    normalized["risk_reward"] = safe_float(
        vision.get("risk_reward")
    )

    normalized["decision"] = vision.get(
        "decision",
        "",
    )

    normalized["summary"] = vision.get(
        "summary",
        "",
    )

    normalized["why"] = vision.get(
        "why",
        "",
    )

    normalized["conditions"] = vision.get(
        "conditions",
        [],
    )

    normalized["generated_by"] = vision.get(
        "generated_by",
        "Gemini",
    )

    return normalized
    # ============================================================
# MARKET STRUCTURE
# ============================================================

def extract_market_structure(
    vision: dict,
) -> dict:

    structure = vision.get(
        "market_structure",
        {},
    )

    return {

        "bos": bool(
            structure.get("bos", False)
        ),

        "choch": bool(
            structure.get("choch", False)
        ),

        "mss": bool(
            structure.get("mss", False)
        ),

        "trend_direction": structure.get(
            "trend_direction",
            "",
        ),

        "breakout": bool(
            structure.get(
                "breakout",
                False,
            )
        ),

        "pullback": bool(
            structure.get(
                "pullback",
                False,
            )
        ),

    }


# ============================================================
# SMART MONEY CONCEPTS
# ============================================================

def extract_smc(
    vision: dict,
) -> dict:

    smc = vision.get(
        "smc",
        {},
    )

    return {

        "order_block":
            smc.get(
                "order_block"
            ),

        "demand_zone":
            smc.get(
                "demand_zone"
            ),

        "supply_zone":
            smc.get(
                "supply_zone"
            ),

        "fvg":
            smc.get(
                "fvg"
            ),

        "liquidity":
            smc.get(
                "liquidity"
            ),

        "weak_high":
            bool(
                smc.get(
                    "weak_high",
                    False,
                )
            ),

        "weak_low":
            bool(
                smc.get(
                    "weak_low",
                    False,
                )
            ),

        "equal_high":
            bool(
                smc.get(
                    "equal_high",
                    False,
                )
            ),

        "equal_low":
            bool(
                smc.get(
                    "equal_low",
                    False,
                )
            ),

    }
    # ============================================================
# BUILD ANALYSIS CONTEXT
# ============================================================

async def build_analysis_context(
    symbol: str,
    image_bytes: bytes,
    mime_type: str,
    interval: str = "1h",
):

    market = await build_market_context(
        symbol,
        interval,
    )

    if image_bytes is not None and mime_type is not None:
        raw_vision = await build_vision_context(
            image_bytes=image_bytes,
            mime_type=mime_type,
            market_context=market,
        )
    else:
        raw_vision = {}

    vision = normalize_vision_result(
        raw_vision,
    )

    vision["market_structure"] = extract_market_structure(
        raw_vision
    )

    vision["smc"] = extract_smc(
        raw_vision
    )

    return {
        "market": market,
        "vision": vision,
        "raw": raw_vision,
    }
    # ============================================================
# SMART MONEY ANALYSIS
# ============================================================

class SmartMoneyAnalyzer:

    def __init__(
        self,
        market: MarketContext,
        vision: dict,
    ):

        self.market = market
        self.vision = vision

        self.structure = vision[
            "market_structure"
        ]

        self.smc = vision["smc"]

        self.score = 50

        self.reasons = []

    # =====================================================

    def analyse_bos(self):

        if self.structure["bos"]:

            self.score += 10

            self.reasons.append(
                "Break Of Structure confirmé."
            )

    # =====================================================

    def analyse_choch(self):

        if self.structure["choch"]:

            self.score += 12

            self.reasons.append(
                "CHoCH détecté."
            )

    # =====================================================

    def analyse_mss(self):

        if self.structure["mss"]:

            self.score += 8

            self.reasons.append(
                "Market Structure Shift."
            )

    # =====================================================

    def analyse_breakout(self):

        if self.structure["breakout"]:

            self.score += 8

            self.reasons.append(
                "Cassure confirmée."
            )

    # =====================================================

    def analyse_pullback(self):

        if self.structure["pullback"]:

            self.score += 5

            self.reasons.append(
                "Retracement propre."
            )
                # =====================================================

    def analyse_order_block(self):

        if self.smc["order_block"]:

            self.score += 10

            self.reasons.append(
                "Order Block présent."
            )

    # =====================================================

    def analyse_fvg(self):

        if self.smc["fvg"]:

            self.score += 8

            self.reasons.append(
                "Fair Value Gap."
            )

    # =====================================================

    def analyse_supply(self):

        if self.smc["supply_zone"]:

            self.score += 6

            self.reasons.append(
                "Supply Zone."
            )

    # =====================================================

    def analyse_demand(self):

        if self.smc["demand_zone"]:

            self.score += 6

            self.reasons.append(
                "Demand Zone."
            )

    # =====================================================

    def analyse_liquidity(self):

        if self.smc["liquidity"]:

            self.score += 6

            self.reasons.append(
                "Liquidité détectée."
            )
                # =====================================================

    def analyse_equal_high(self):

        if self.smc["equal_high"]:

            self.score += 4

            self.reasons.append(
                "Equal High."
            )

    # =====================================================

    def analyse_equal_low(self):

        if self.smc["equal_low"]:

            self.score += 4

            self.reasons.append(
                "Equal Low."
            )

    # =====================================================

    def analyse_weak_high(self):

        if self.smc["weak_high"]:

            self.score -= 5

            self.reasons.append(
                "Weak High."
            )

    # =====================================================

    def analyse_weak_low(self):

        if self.smc["weak_low"]:

            self.score -= 5

            self.reasons.append(
                "Weak Low."
            )
                # =====================================================

    def analyse_price_action(self):

        patterns = self.vision.get(
            "patterns",
            [],
        )

        candles = self.vision.get(
            "candlestick_patterns",
            [],
        )

        if len(patterns):

            self.score += min(
                len(patterns) * 2,
                8,
            )

        if len(candles):

            self.score += min(
                len(candles) * 2,
                8,
            )

        return

    # =====================================================

    def analyse(self):

        self.analyse_bos()

        self.analyse_choch()

        self.analyse_mss()

        self.analyse_breakout()

        self.analyse_pullback()

        self.analyse_order_block()

        self.analyse_fvg()

        self.analyse_supply()

        self.analyse_demand()

        self.analyse_liquidity()

        self.analyse_equal_high()

        self.analyse_equal_low()

        self.analyse_weak_high()

        self.analyse_weak_low()

        self.analyse_price_action()

        self.score = normalize_score(
            self.score
        )

        return {

            "score": self.score,

            "reasons": self.reasons,

        }
        # ============================================================
# CONTRADICTION ANALYZER
# ============================================================

class ContradictionAnalyzer:

    def __init__(
        self,
        market: MarketContext,
        vision: dict,
        smc: dict,
    ):

        self.market = market

        self.vision = vision

        self.smc = smc

        self.penalty = 0

        self.reasons = []

    # =====================================================

    def trend_vs_signal(self):

        trend = self.market.get(
            "trend"
        )

        signal = self.vision.get(
            "signal",
            "ATTENDRE",
        )

        if (
            trend == "HAUSSIERE"
            and signal == "VENTE"
        ):

            self.penalty += 25

            self.reasons.append(
                "Signal vendeur contre la tendance."
            )

        if (
            trend == "BAISSIERE"
            and signal == "ACHAT"
        ):

            self.penalty += 25

            self.reasons.append(
                "Signal acheteur contre la tendance."
            )

    # =====================================================

    def adx_filter(self):

        adx = self.market.get(
            "adx"
        )

        if adx is None:

            return

        if adx < 18:

            self.penalty += 15

            self.reasons.append(
                "ADX trop faible."
            )

    # =====================================================

    def volume_filter(self):

        rv = self.market.get(
            "relative_volume"
        )

        if rv is None:

            return

        if rv < 0.90:

            self.penalty += 15

            self.reasons.append(
                "Volume insuffisant."
            )
                # =====================================================

    def breakout_without_volume(self):

        breakout = self.market.get(
            "breakout"
        )

        rv = self.market.get(
            "relative_volume"
        )

        if (
            breakout
            and rv
            and rv < 1.20
        ):

            self.penalty += 20

            self.reasons.append(
                "Breakout sans volume."
            )

    # =====================================================

    def weak_structure(self):

        if self.smc[
            "weak_high"
        ]:

            self.penalty += 10

            self.reasons.append(
                "Weak High."
            )

        if self.smc[
            "weak_low"
        ]:

            self.penalty += 10

            self.reasons.append(
                "Weak Low."
            )

    # =====================================================

    def volatility_filter(self):

        volatility = self.market.get(
            "volatility"
        )

        if volatility is None:

            return

        if volatility > 8:

            self.penalty += 8

            self.reasons.append(
                "Volatilité excessive."
            )
                # =====================================================

    def ema_filter(self):

        ema20 = self.market.get(
            "ema20"
        )

        ema50 = self.market.get(
            "ema50"
        )

        ema100 = self.market.get(
            "ema100"
        )

        if None in (
            ema20,
            ema50,
            ema100,
        ):

            return

        signal = self.vision.get(
            "signal",
            "",
        )

        if (
            signal == "ACHAT"
            and ema20 < ema50
        ):

            self.penalty += 15

            self.reasons.append(
                "EMA défavorables."
            )

        if (
            signal == "VENTE"
            and ema20 > ema50
        ):

            self.penalty += 15

            self.reasons.append(
                "EMA défavorables."
            )

    # =====================================================

    def momentum_filter(self):

        momentum = self.market.get(
            "momentum"
        )

        if momentum is None:

            return

        signal = self.vision.get(
            "signal",
            ""
        )

        if (
            signal == "ACHAT"
            and momentum < 0
        ):

            self.penalty += 15

            self.reasons.append(
                "Momentum baissier."
            )

        if (
            signal == "VENTE"
            and momentum > 0
        ):

            self.penalty += 15

            self.reasons.append(
                "Momentum haussier."
            )
                # =====================================================

    def analyse(self):

        self.trend_vs_signal()

        self.adx_filter()

        self.volume_filter()

        self.breakout_without_volume()

        self.weak_structure()

        self.volatility_filter()

        self.ema_filter()

        self.momentum_filter()

        return {

            "penalty": min(
                self.penalty,
                100,
            ),

            "reasons": self.reasons,

        }
        # ============================================================
# TRADE PLANNER
# ============================================================

class TradePlanner:

    def __init__(
        self,
        market: MarketContext,
        vision: dict,
    ):

        self.market = market
        self.vision = vision

        self.entry = None
        self.stop = None

        self.tp1 = None
        self.tp2 = None
        self.tp3 = None
        self.tp4 = None

        self.break_even = None

    # =====================================================

    @property
    def direction(self):

        return self.vision.get(
            "signal",
            "ATTENDRE",
        )

    @property
    def price(self):

        return self.market.get("price")

    @property
    def atr(self):

        return self.market.get("atr")

    @property
    def support(self):

        return self.market.get("support")

    @property
    def resistance(self):

        return self.market.get(
            "resistance"
        )
            # =====================================================

    def compute_entry(self):

        if self.direction == "ACHAT":

            if self.support:

                self.entry = max(
                    self.price,
                    self.support
                    + self.atr * 0.20,
                )

            else:

                self.entry = self.price

        elif self.direction == "VENTE":

            if self.resistance:

                self.entry = min(
                    self.price,
                    self.resistance
                    - self.atr * 0.20,
                )

            else:

                self.entry = self.price

        else:

            self.entry = self.price

        self.entry = round_price(
            self.entry
        )
            # =====================================================

    def compute_stop_loss(self):

    # =====================================================
    # Sécurités
    # =====================================================

    if self.entry is None:
        self.stop = None
        return

    atr = self.atr or 0
    volatility = self.market.get("volatility") or 0

    # Distance minimale
    atr_multiplier = 1.50

    if volatility > 6:
        atr_multiplier = 2.00
    elif volatility < 2:
        atr_multiplier = 1.20

    # =====================================================
    # ACHAT
    # =====================================================

    if self.direction == "ACHAT":

        candidates = []

        if self.support is not None:
            candidates.append(self.support)

        if atr > 0:
            candidates.append(
                self.entry - atr * atr_multiplier
            )

        # Stop proposé par Gemini
        ai_stop = self.vision.get("stop_loss")

        if ai_stop:
            candidates.append(ai_stop)

        if candidates:
            self.stop = min(candidates)
        else:
            self.stop = self.entry * 0.98

    # =====================================================
    # VENTE
    # =====================================================

    elif self.direction == "VENTE":

        candidates = []

        if self.resistance is not None:
            candidates.append(self.resistance)

        if atr > 0:
            candidates.append(
                self.entry + atr * atr_multiplier
            )

        ai_stop = self.vision.get("stop_loss")

        if ai_stop:
            candidates.append(ai_stop)

        if candidates:
            self.stop = max(candidates)
        else:
            self.stop = self.entry * 1.02

    else:

        self.stop = None

    self.stop = round_price(self.stop)
    
            # =====================================================

def compute_take_profits(self):

    if self.entry is None:
        return

    atr = self.atr or 0

    resistance = self.resistance
    support = self.support

    ai_tp = self.vision.get("take_profit")

    # =====================================================
    # ACHAT
    # =====================================================

    if self.direction == "ACHAT":

        # TP1 = première résistance
        if resistance:
            self.tp1 = resistance
        else:
            self.tp1 = self.entry + atr

        # TP2 = objectif principal
        if ai_tp:
            self.tp2 = max(
                ai_tp,
                self.entry + atr * 2
            )
        else:
            self.tp2 = self.entry + atr * 2

        # TP3 = extension
        self.tp3 = max(
            self.tp2,
            self.entry + atr * 3.5
        )

        # TP4 = objectif final
        self.tp4 = max(
            self.tp3,
            self.entry + atr * 5
        )

    # =====================================================
    # VENTE
    # =====================================================

    elif self.direction == "VENTE":

        # TP1 = premier support
        if support:
            self.tp1 = support
        else:
            self.tp1 = self.entry - atr

        # TP2 = objectif principal
        if ai_tp:
            self.tp2 = min(
                ai_tp,
                self.entry - atr * 2
            )
        else:
            self.tp2 = self.entry - atr * 2

        # TP3 = extension
        self.tp3 = min(
            self.tp2,
            self.entry - atr * 3.5
        )

        # TP4 = objectif final
        self.tp4 = min(
            self.tp3,
            self.entry - atr * 5
        )

    else:

        self.tp1 = None
        self.tp2 = None
        self.tp3 = None
        self.tp4 = None

    self.tp1 = round_price(self.tp1)
    self.tp2 = round_price(self.tp2)
    self.tp3 = round_price(self.tp3)
    self.tp4 = round_price(self.tp4)

# =====================================================

def compute_break_even(self):

        if self.direction == "ACHAT":

            self.break_even = round_price(

                self.entry
                + self.atr,

            )

        elif self.direction == "VENTE":

            self.break_even = round_price(

                self.entry
                - self.atr,

            )

    # =====================================================

def compute_rr(self):

    if (
        self.entry is None
        or self.stop is None
    ):
        return None

    results = {}

    risk = abs(
        self.entry - self.stop
    )

    if risk == 0:
        return None

    targets = {
        "tp1": self.tp1,
        "tp2": self.tp2,
        "tp3": self.tp3,
        "tp4": self.tp4,
    }

    for name, target in targets.items():

        if target is None:
            results[name] = None
            continue

        reward = abs(
            target - self.entry
        )

        results[name] = round(
            reward / risk,
            2,
        )

    valid_rr = [
        rr
        for rr in results.values()
        if rr is not None
    ]

    results["best"] = (
        max(valid_rr)
        if valid_rr
        else None
    )

    results["recommended"] = (
        results["tp2"]
        if results["tp2"] is not None
        else results["tp1"]
    )

    return results

    # =====================================================

    def build(self):

        self.compute_entry()

        self.compute_stop_loss()

        self.compute_take_profits()

        self.compute_break_even()

        return {

            "direction":
                self.direction,

            "entry":
                self.entry,

            "stop_loss":
                self.stop,

            "tp1":
                self.tp1,

            "tp2":
                self.tp2,

            "tp3":
                self.tp3,

            "tp4":
                self.tp4,

            "break_even":
                self.break_even,

            "risk_reward":
                self.compute_rr(),

        }
        # ============================================================
# DECISION ENGINE
# ============================================================

class DecisionEngine:

    def __init__(
        self,
        market: MarketContext,
        vision: dict,
        smc_result: dict,
        contradiction_result: dict,
        trade_plan: dict,
    ):

        self.market = market
        self.vision = vision
        self.smc = smc_result
        self.contradictions = contradiction_result
        self.trade = trade_plan

        self.score = 0
        self.decision = "ATTENDRE"

        self.reasons = []

    # =====================================================

    def score_market(self):

        self.score += (
            self.market.get(
                "market_score",
                50,
            )
            * 0.30
        )

    # =====================================================

    def score_smc(self):

        self.score += (
            self.smc["score"]
            * 0.30
        )

    # =====================================================

    def score_ai(self):

        self.score += (
            self.vision.get(
                "confidence",
                50,
            )
            * 0.20
        )

    # =====================================================

    def remove_penalties(self):

        self.score -= (
            self.contradictions[
                "penalty"
            ]
            * 0.25
        )

    # =====================================================

    def normalize(self):

        self.score = normalize_score(
            self.score
        )
            # =====================================================

def validate_rr(self):

    rr = self.trade.get(
        "risk_reward",
        {},
    ).get("recommended")

    if rr is None:
        self.reasons.append(
            "Risk Reward inconnu."
        )
        return False

    if rr < 2:
        self.reasons.append(
            "Risk Reward inférieur à 2."
        )
        return False

    return True
            # =====================================================

    def validate_trend(self):

        trend = self.market.get(
            "trend"
        )

        signal = self.vision.get(
            "signal",
            "",
        )

        if (
            trend == "HAUSSIERE"
            and signal == "VENTE"
        ):

            self.reasons.append(
                "Signal contraire à la tendance."
            )

            return False

        if (
            trend == "BAISSIERE"
            and signal == "ACHAT"
        ):

            self.reasons.append(
                "Signal contraire à la tendance."
            )

            return False

        return True

    # =====================================================

    def validate_adx(self):

        adx = self.market.get(
            "adx"
        )

        if adx is None:

            return True

        if adx < 18:

            self.reasons.append(
                "Tendance trop faible."
            )

            return False

        return True
            # =====================================================

def build_decision(self):

    # =====================================================
    # Construction du score global
    # =====================================================

    self.score_market()
    self.score_smc()
    self.score_ai()
    self.remove_penalties()
    self.normalize()

    signal = self.vision.get(
        "signal",
        "ATTENDRE",
    )

    validations = {
        "rr": self.validate_rr(),
        "volume": self.validate_volume(),
        "trend": self.validate_trend(),
        "adx": self.validate_adx(),
    }

    failed = [
        key
        for key, value in validations.items()
        if not value
    ]

    # =====================================================
    # Décision
    # =====================================================

    if len(failed) >= 3:
        self.decision = "ATTENDRE"
        self.reasons.append(
            "Trop de critères bloquants."
        )
        return

    if self.score >= 85 and len(failed) == 0:
        self.decision = signal
        self.reasons.append(
            "Toutes les conditions sont réunies."
        )
        return

    if self.score >= 75 and len(failed) <= 1:
        self.decision = signal
        self.reasons.append(
            "Signal valide avec un risque maîtrisé."
        )
        return

    if self.score >= 65:
        self.decision = "ATTENDRE"
        self.reasons.append(
            "Confiance insuffisante."
        )
        return

    self.decision = "ATTENDRE"
    self.reasons.append(
        "Score global trop faible."
    )
                # =====================================================

    def export(self):

        self.build_decision()

        return {

            "decision":
                self.decision,

            "confidence":
                self.score,

            "signal":
                self.vision.get(
                    "signal",
                    "ATTENDRE",
                ),

            "reasons":
                self.reasons,

            "market_score":
                self.market.get(
                    "market_score"
                ),

            "smc_score":
                self.smc["score"],

            "penalty":
                self.contradictions[
                    "penalty"
                ],

        }
        # ============================================================
# TRADE MANAGER
# ============================================================

class TradeManager:

    def __init__(
        self,
        market: MarketContext,
        trade: dict,
        decision: dict,
    ):

        self.market = market
        self.trade = trade
        self.decision = decision

        self.actions = []

    # =====================================================

    @property
    def direction(self):

        return self.trade.get(
            "direction",
            "ATTENDRE",
        )

    @property
    def entry(self):

        return self.trade.get("entry")

    @property
    def stop(self):

        return self.trade.get(
            "stop_loss"
        )

    @property
    def tp1(self):

        return self.trade.get("tp1")

    @property
    def tp2(self):

        return self.trade.get("tp2")

    @property
    def tp3(self):

        return self.trade.get("tp3")

    @property
    def tp4(self):

        return self.trade.get("tp4")

    @property
    def break_even(self):

        return self.trade.get(
            "break_even"
        )
            # =====================================================

    def build_break_even(self):

        return {

            "enabled": True,

            "trigger_price":
                self.break_even,

            "new_stop":
                self.entry,

            "message":
                (
                    "Déplacer le Stop "
                    "Loss au prix d'entrée."
                ),

        }

    # =====================================================

    def build_partial_take_profit(self):

        return [

            {

                "target":
                    self.tp1,

                "close":
                    30,

            },

            {

                "target":
                    self.tp2,

                "close":
                    30,

            },

            {

                "target":
                    self.tp3,

                "close":
                    20,

            },

            {

                "target":
                    self.tp4,

                "close":
                    20,

            },

        ]
            # =====================================================

    def build_trailing_stop(self):

        atr = self.market.get("atr")

        if atr is None:

            return None

        return {

            "enabled": True,

            "distance":
                round_price(
                    atr * 1.20
                ),

            "activation":
                self.tp2,

            "message":
                (
                    "Activer un "
                    "Trailing Stop."
                ),

        }
            # =====================================================

    def build_invalidation(self):

        trend = self.market.get(
            "trend"
        )

        signal = self.direction

        rules = []

        if signal == "ACHAT":

            rules.extend(

                [

                    "Cassure du support.",

                    "Retour sous EMA20.",

                    "Momentum négatif.",

                    "MACD baissier.",

                ]

            )

        elif signal == "VENTE":

            rules.extend(

                [

                    "Cassure de la résistance.",

                    "Retour au-dessus EMA20.",

                    "Momentum positif.",

                    "MACD haussier.",

                ]

            )

        if trend == "NEUTRE":

            rules.append(

                "Marché sans tendance."

            )

        return rules
            # =====================================================

    def export(self):

        return {

            "break_even":

                self.build_break_even(),

            "partial_take_profit":

                self.build_partial_take_profit(),

            "trailing_stop":

                self.build_trailing_stop(),

            "runner_target":

                self.tp4,

            "invalidation":

                self.build_invalidation(),

        }
        # ============================================================
# REPORT BUILDER
# ============================================================

class ReportBuilder:

    def __init__(
        self,
        market: MarketContext,
        vision: dict,
        smc: dict,
        contradictions: dict,
        trade: dict,
        decision: dict,
        trade_manager: dict,
    ):

        self.market = market
        self.vision = vision
        self.smc = smc
        self.contradictions = contradictions
        self.trade = trade
        self.decision = decision
        self.trade_manager = trade_manager

    # =====================================================

    def build_summary(self):

        return {

            "symbol":
                self.market.get("pair"),

            "interval":
                self.market.get("interval"),

            "generated_at":
                self.market.get(
                    "generated_at"
                ),

            "decision":
                self.decision["decision"],

            "confidence":
                self.decision[
                    "confidence"
                ],

            "market_score":
                self.market.get(
                    "market_score"
                ),

            "trend":
                self.market.get(
                    "trend"
                ),

            "trend_strength":
                self.market.get(
                    "trend_strength"
                ),

        }
            # =====================================================

    def build_market_section(self):

        return {

            "price":
                self.market.get(
                    "price"
                ),

            "rsi":
                self.market.get(
                    "rsi"
                ),

            "macd":
                self.market.get(
                    "macd"
                ),

            "macd_signal":
                self.market.get(
                    "macd_signal"
                ),

            "macd_hist":
                self.market.get(
                    "macd_hist"
                ),

            "ema20":
                self.market.get(
                    "ema20"
                ),

            "ema50":
                self.market.get(
                    "ema50"
                ),

            "ema100":
                self.market.get(
                    "ema100"
                ),

            "ema200":
                self.market.get(
                    "ema200"
                ),

            "atr":
                self.market.get(
                    "atr"
                ),

            "adx":
                self.market.get(
                    "adx"
                ),

            "relative_volume":
                self.market.get(
                    "relative_volume"
                ),

            "volatility":
                self.market.get(
                    "volatility"
                ),

            "momentum":
                self.market.get(
                    "momentum"
                ),

        }
            # =====================================================

    def build_trade_section(self):

        return {

            "direction":
                self.trade[
                    "direction"
                ],

            "entry":
                self.trade[
                    "entry"
                ],

            "stop_loss":
                self.trade[
                    "stop_loss"
                ],

            "tp1":
                self.trade[
                    "tp1"
                ],

            "tp2":
                self.trade[
                    "tp2"
                ],

            "tp3":
                self.trade[
                    "tp3"
                ],

            "tp4":
                self.trade[
                    "tp4"
                ],

            "break_even":
                self.trade[
                    "break_even"
                ],

            "risk_reward":
                self.trade[
                    "risk_reward"
                ],

        }
            # =====================================================

    def build_analysis_section(self):

        return {

            "vision":

                self.vision,

            "smc":

                self.smc,

            "contradictions":

                self.contradictions,

            "decision":

                self.decision,

        }

    # =====================================================

    def build_trade_management(self):

        return self.trade_manager
            # =====================================================

    def export(self):

        return {

            "summary":

                self.build_summary(),

            "market":

                self.build_market_section(),

            "analysis":

                self.build_analysis_section(),

            "trade":

                self.build_trade_section(),

            "trade_management":

                self.build_trade_management(),

        }
        # ============================================================
# ANALYSIS ENGINE
# ============================================================

async def analyze_engine(
    symbol: str,
    image_bytes: bytes,
    mime_type: str,
    interval: str = "1h",
):

    try:

        # ===================================================
        # BUILD CONTEXT
        # ===================================================

        context = await build_analysis_context(
            symbol=symbol,
            image_bytes=image_bytes,
            mime_type=mime_type,
            interval=interval,
        )

        market = context["market"]

        vision = context["vision"]

        # ===================================================
        # SMART MONEY ANALYSIS
        # ===================================================

        smc_analyzer = SmartMoneyAnalyzer(
            market,
            vision,
        )

        smc_result = smc_analyzer.analyse()

        # ===================================================
        # CONTRADICTIONS
        # ===================================================

        contradiction_engine = ContradictionAnalyzer(
            market,
            vision,
            vision["smc"],
        )

        contradiction_result = (
            contradiction_engine.analyse()
        )

        # ===================================================
        # TRADE PLAN
        # ===================================================

        planner = TradePlanner(
            market,
            vision,
        )

        trade_plan = planner.build()

        # ===================================================
        # DECISION
        # ===================================================

        decision_engine = DecisionEngine(
            market=market,
            vision=vision,
            smc_result=smc_result,
            contradiction_result=contradiction_result,
            trade_plan=trade_plan,
        )

        decision = decision_engine.export()

        # ===================================================
        # TRADE MANAGEMENT
        # ===================================================

        trade_manager = TradeManager(
            market=market,
            trade=trade_plan,
            decision=decision,
        )

        management = trade_manager.export()

        # ===================================================
        # REPORT
        # ===================================================

        report = ReportBuilder(
            market=market,
            vision=vision,
            smc=smc_result,
            contradictions=contradiction_result,
            trade=trade_plan,
            decision=decision,
            trade_manager=management,
        )

        return report.export()

    except AnalysisEngineError as exc:

        return {

            "success": False,

            "error": str(exc),

            "generated_at": utc_now(),

        }

    except Exception as exc:

        return {

            "success": False,

            "error": f"Analysis Engine Error : {exc}",

            "generated_at": utc_now(),

        }


# ============================================================
# SHORTCUT
# ============================================================

async def analyze(
    symbol,
    image_bytes=None,
    mime_type=None,
):

    return await analyze_engine(
        symbol=symbol,
        image_bytes=image_bytes,
        mime_type=mime_type,
    )
    
