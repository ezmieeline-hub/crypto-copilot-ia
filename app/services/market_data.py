import math
import statistics
import httpx

BINANCE_KLINES_URL = "https://api.binance.com/api/v3/klines"


# ============================================================
# BINANCE
# ============================================================

async def get_klines(symbol: str, interval: str = "1h", limit: int = 300):
    pair = symbol.upper().strip().replace("/", "").replace("USDT", "") + "USDT"

    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get(
            BINANCE_KLINES_URL,
            params={
                "symbol": pair,
                "interval": interval,
                "limit": limit,
            },
        )

        r.raise_for_status()

        data = r.json()

    return [
        {
            "open_time": k[0],
            "open": float(k[1]),
            "high": float(k[2]),
            "low": float(k[3]),
            "close": float(k[4]),
            "volume": float(k[5]),
        }
        for k in data
    ]


# ============================================================
# MOVING AVERAGES
# ============================================================

def compute_sma(values, period):

    if len(values) < period:
        return None

    return round(sum(values[-period:]) / period, 6)


def compute_ema(values, period):

    if len(values) < period:
        return None

    multiplier = 2 / (period + 1)

    ema = values[0]

    for price in values[1:]:

        ema = ((price - ema) * multiplier) + ema

    return round(ema, 6)


def compute_ema_series(values, period):

    multiplier = 2 / (period + 1)

    ema = values[0]

    result = [ema]

    for value in values[1:]:

        ema = ((value - ema) * multiplier) + ema

        result.append(ema)

    return result


# ============================================================
# RSI WILDER
# ============================================================

def compute_rsi(closes, period=14):

    if len(closes) <= period:
        return None

    gains = []
    losses = []

    for i in range(1, len(closes)):

        delta = closes[i] - closes[i - 1]

        gains.append(max(delta, 0))

        losses.append(abs(min(delta, 0)))

    avg_gain = sum(gains[:period]) / period

    avg_loss = sum(losses[:period]) / period

    for i in range(period, len(gains)):

        avg_gain = ((avg_gain * (period - 1)) + gains[i]) / period

        avg_loss = ((avg_loss * (period - 1)) + losses[i]) / period

    if avg_loss == 0:

        return 100

    rs = avg_gain / avg_loss

    rsi = 100 - (100 / (1 + rs))

    return round(rsi, 2)


# ============================================================
# MACD
# ============================================================

def compute_macd(
    closes,
    fast=12,
    slow=26,
    signal=9,
):

    if len(closes) < slow + signal:

        return None, None, None

    ema_fast = compute_ema_series(closes, fast)

    ema_slow = compute_ema_series(closes, slow)

    offset = len(ema_fast) - len(ema_slow)

    macd_line = []

    for i in range(len(ema_slow)):

        macd_line.append(
            ema_fast[i + offset] - ema_slow[i]
        )

    signal_line = compute_ema_series(
        macd_line,
        signal,
    )

    histogram = macd_line[-1] - signal_line[-1]

    return (

        round(macd_line[-1], 6),

        round(signal_line[-1], 6),

        round(histogram, 6),

    )


# ============================================================
# EMA UTILITAIRES
# ============================================================

def compute_ema20(closes):

    return compute_ema(closes, 20)


def compute_ema50(closes):

    return compute_ema(closes, 50)


def compute_ema100(closes):

    return compute_ema(closes, 100)


def compute_ema200(closes):

    return compute_ema(closes, 200)
    # ============================================================
# ATR
# ============================================================

def compute_atr(klines, period=14):

    if len(klines) <= period:
        return None

    true_ranges = []

    for i in range(1, len(klines)):

        high = klines[i]["high"]
        low = klines[i]["low"]
        prev_close = klines[i - 1]["close"]

        tr = max(
            high - low,
            abs(high - prev_close),
            abs(low - prev_close),
        )

        true_ranges.append(tr)

    atr = sum(true_ranges[:period]) / period

    for tr in true_ranges[period:]:

        atr = ((atr * (period - 1)) + tr) / period

    return round(atr, 6)


# ============================================================
# ADX
# ============================================================

def compute_adx(klines, period=14):

    if len(klines) < period * 2:
        return None

    plus_dm = []
    minus_dm = []
    tr_list = []

    for i in range(1, len(klines)):

        current = klines[i]
        previous = klines[i - 1]

        up_move = current["high"] - previous["high"]
        down_move = previous["low"] - current["low"]

        plus_dm.append(up_move if up_move > down_move and up_move > 0 else 0)
        minus_dm.append(down_move if down_move > up_move and down_move > 0 else 0)

        tr = max(
            current["high"] - current["low"],
            abs(current["high"] - previous["close"]),
            abs(current["low"] - previous["close"]),
        )

        tr_list.append(tr)

    atr = sum(tr_list[:period])

    plus = sum(plus_dm[:period])

    minus = sum(minus_dm[:period])

    dx_values = []

    for i in range(period, len(tr_list)):

        atr = atr - (atr / period) + tr_list[i]

        plus = plus - (plus / period) + plus_dm[i]

        minus = minus - (minus / period) + minus_dm[i]

        if atr == 0:
            continue

        plus_di = (100 * plus) / atr

        minus_di = (100 * minus) / atr

        total = plus_di + minus_di

        if total == 0:
            dx = 0
        else:
            dx = (abs(plus_di - minus_di) / total) * 100

        dx_values.append(dx)

    if not dx_values:
        return None

    return round(sum(dx_values[-period:]) / len(dx_values[-period:]), 2)


# ============================================================
# VOLUME
# ============================================================

def compute_average_volume(klines, period=20):

    if len(klines) < period:
        return None

    volumes = [k["volume"] for k in klines[-period:]]

    return round(sum(volumes) / period, 2)


def compute_relative_volume(klines, period=20):

    avg = compute_average_volume(klines, period)

    if avg in (None, 0):
        return None

    current = klines[-1]["volume"]

    return round(current / avg, 2)


# ============================================================
# VOLATILITY
# ============================================================

def compute_volatility(closes, period=20):

    if len(closes) < period:
        return None

    recent = closes[-period:]

    mean = statistics.mean(recent)

    if mean == 0:
        return None

    std = statistics.stdev(recent)

    return round((std / mean) * 100, 2)


# ============================================================
# MOMENTUM
# ============================================================

def compute_momentum(closes, period=10):

    if len(closes) <= period:
        return None

    momentum = closes[-1] - closes[-1 - period]

    return round(momentum, 6)


# ============================================================
# TREND STRENGTH
# ============================================================

def compute_trend_strength(rsi, macd_hist, adx):

    score = 0

    if rsi is not None:

        if rsi > 60:
            score += 25
        elif rsi > 55:
            score += 15
        elif rsi < 40:
            score -= 25

    if macd_hist is not None:

        if macd_hist > 0:
            score += 25
        else:
            score -= 25

    if adx is not None:

        if adx > 35:
            score += 35
        elif adx > 25:
            score += 20
        elif adx < 15:
            score -= 15

    if score >= 70:
        return "Très forte"

    if score >= 45:
        return "Forte"

    if score >= 20:
        return "Modérée"

    if score >= 0:
        return "Faible"

    return "Très faible"
    # ============================================================
# SUPPORT / RESISTANCE
# ============================================================

def compute_support_resistance(klines, lookback=30):

    recent = klines[-lookback:] if len(klines) >= lookback else klines

    lows = [k["low"] for k in recent]
    highs = [k["high"] for k in recent]

    return (
        round(min(lows), 6),
        round(max(highs), 6),
    )


def compute_support_distance(price, support):

    if support is None:
        return None

    return round(((price - support) / price) * 100, 2)


def compute_resistance_distance(price, resistance):

    if resistance is None:
        return None

    return round(((resistance - price) / price) * 100, 2)


# ============================================================
# BREAKOUT
# ============================================================

def detect_breakout(klines, resistance):

    if resistance is None:
        return False

    close = klines[-1]["close"]

    return close > resistance


def detect_breakdown(klines, support):

    if support is None:
        return False

    close = klines[-1]["close"]

    return close < support


# ============================================================
# PULLBACK
# ============================================================

def detect_pullback(klines, ema20):

    if ema20 is None:
        return False

    close = klines[-1]["close"]

    low = klines[-1]["low"]

    tolerance = ema20 * 0.003

    return low <= ema20 + tolerance


# ============================================================
# RISK / REWARD
# ============================================================

def compute_risk_reward(entry, stop_loss, take_profit):

    if None in (entry, stop_loss, take_profit):
        return None

    risk = abs(entry - stop_loss)

    reward = abs(take_profit - entry)

    if risk == 0:
        return None

    return round(reward / risk, 2)


# ============================================================
# TAKE PROFITS
# ============================================================

def compute_take_profits(entry, atr, direction="LONG"):

    if entry is None or atr is None:
        return None, None, None

    if direction.upper() == "LONG":

        tp1 = entry + atr
        tp2 = entry + atr * 2
        tp3 = entry + atr * 3

    else:

        tp1 = entry - atr
        tp2 = entry - atr * 2
        tp3 = entry - atr * 3

    return (
        round(tp1, 6),
        round(tp2, 6),
        round(tp3, 6),
    )


# ============================================================
# STOP LOSS
# ============================================================

def compute_stop_loss(entry, atr, direction="LONG"):

    if entry is None or atr is None:
        return None

    if direction.upper() == "LONG":
        return round(entry - atr * 1.5, 6)

    return round(entry + atr * 1.5, 6)


# ============================================================
# POSITION SIZE
# ============================================================

def compute_position_size(balance, risk_percent, entry, stop_loss):

    if None in (balance, risk_percent, entry, stop_loss):
        return None

    risk_amount = balance * (risk_percent / 100)

    stop_distance = abs(entry - stop_loss)

    if stop_distance == 0:
        return None

    size = risk_amount / stop_distance

    return round(size, 4)


# ============================================================
# MARKET SCORE
# ============================================================

def compute_market_score(
    rsi,
    macd_hist,
    adx,
    relative_volume,
):

    score = 50

    if rsi is not None:

        if rsi > 60:
            score += 10
        elif rsi < 40:
            score -= 10

    if macd_hist is not None:

        score += 10 if macd_hist > 0 else -10

    if adx is not None:

        if adx > 30:
            score += 10
        elif adx < 15:
            score -= 5

    if relative_volume is not None:

        if relative_volume > 1.5:
            score += 10

        elif relative_volume < 0.8:
            score -= 5

    return max(0, min(100, int(score)))


# ============================================================
# MARKET SUMMARY
# ============================================================

def build_market_summary(
    trend,
    trend_strength,
    rsi,
    macd_hist,
    adx,
):

    lines = []

    lines.append(f"Tendance : {trend}")

    lines.append(f"Force : {trend_strength}")

    if rsi is not None:
        lines.append(f"RSI : {rsi}")

    if macd_hist is not None:

        if macd_hist > 0:
            lines.append("MACD haussier")

        else:
            lines.append("MACD baissier")

    if adx is not None:

        if adx > 25:
            lines.append("Tendance solide")

        else:
            lines.append("Marché peu directionnel")

    return " | ".join(lines)
