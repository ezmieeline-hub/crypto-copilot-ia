import httpx

BINANCE_KLINES_URL = "https://api.binance.com/api/v3/klines"


async def get_klines(symbol: str, interval: str = "1h", limit: int = 100):
    pair = symbol.upper().strip().replace("/", "").replace("USDT", "") + "USDT"
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(
            BINANCE_KLINES_URL,
            params={"symbol": pair, "interval": interval, "limit": limit},
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


def compute_rsi(closes, period: int = 14):
    if len(closes) < period + 1:
        return None
    gains, losses = [], []
    for i in range(1, len(closes)):
        diff = closes[i] - closes[i - 1]
        gains.append(max(diff, 0))
        losses.append(max(-diff, 0))
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return round(100 - (100 / (1 + rs)), 2)


def _ema(values, period: int):
    k = 2 / (period + 1)
    ema_vals = [values[0]]
    for v in values[1:]:
        ema_vals.append(v * k + ema_vals[-1] * (1 - k))
    return ema_vals


def compute_macd(closes, fast: int = 12, slow: int = 26, signal: int = 9):
    if len(closes) < slow + signal:
        return None, None, None
    ema_fast = _ema(closes, fast)
    ema_slow = _ema(closes, slow)
    macd_line_full = [f - s for f, s in zip(ema_fast[-len(ema_slow):], ema_slow)]
    signal_line_full = _ema(macd_line_full, signal)
    macd_line = macd_line_full[-1]
    signal_line = signal_line_full[-1]
    histogram = macd_line - signal_line
    return round(macd_line, 2), round(signal_line, 2), round(histogram, 2)


def compute_support_resistance(klines, lookback: int = 30):
    recent = klines[-lookback:] if len(klines) >= lookback else klines
    lows = [k["low"] for k in recent]
    highs = [k["high"] for k in recent]
    return round(min(lows), 6), round(max(highs), 6)
