"""
Module fallback Yahoo Finance — Option A
Couvre XAUUSD, forex, actions quand la source crypto principale est KO
"""
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)

# Mapping symboles utilisateur → Yahoo Finance
YF_MAP = {
    # Métaux
    "XAUUSD": "GC=F",
    "XAGUSD": "SI=F",
    "XPTUSD": "PL=F",
    # Forex
    "EURUSD": "EURUSD=X",
    "GBPUSD": "GBPUSD=X",
    "USDJPY": "USDJPY=X",
    "USDCHF": "USDCHF=X",
    "AUDUSD": "AUDUSD=X",
    "USDCAD": "USDCAD=X",
    "NZDUSD": "NZDUSD=X",
    # Indices
    "SPX500": "^GSPC",
    "NAS100": "^IXIC",
    "DJ30": "^DJI",
    # Actions (exemples)
    "AAPL": "AAPL",
    "TSLA": "TSLA",
    "NVDA": "NVDA",
    "MSFT": "MSFT",
    "GOOGL": "GOOGL",
    # Crypto (fallback YF si besoin)
    "BTCUSD": "BTC-USD",
    "ETHUSD": "ETH-USD",
    "SOLUSD": "SOL-USD",
}


class YahooFallback:
    def __init__(self, cache_ttl: int = 300):
        self.cache_ttl = cache_ttl
        self._cache: Dict[str, Any] = {}
        self._time: Dict[str, datetime] = {}

    def _to_yf(self, symbol: str) -> str:
        s = symbol.upper().replace("/", "").replace("-", "")
        return YF_MAP.get(s, symbol.upper())

    def _valid(self, key: str) -> bool:
        if key not in self._time:
            return False
        return (datetime.now() - self._time[key]).seconds < self.cache_ttl

    def get_ohlcv(
        self,
        symbol: str,
        period: str = "1mo",
        interval: str = "1h"
    ) -> Optional[pd.DataFrame]:
        """
        Récupère l'historique OHLCV
        period: 1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max
        interval: 1m,2m,5m,15m,30m,60m,90m,1h,1d,5d,1wk,1mo,3mo
        """
        key = f"ohlcv_{symbol}_{period}_{interval}"
        if self._valid(key):
            return self._cache[key]

        try:
            yf_sym = self._to_yf(symbol)
            ticker = yf.Ticker(yf_sym)
            df = ticker.history(period=period, interval=interval)

            if df.empty:
                logger.warning(f"[YF] Vide pour {symbol} ({yf_sym})")
                return None

            df = df.reset_index()
            time_col = "Datetime" if "Datetime" in df.columns else "Date"
            df = df.rename(columns={time_col: "timestamp"})
            df = df[["timestamp", "Open", "High", "Low", "Close", "Volume"]]
            df.columns = ["timestamp", "open", "high", "low", "close", "volume"]
            df["timestamp"] = pd.to_datetime(df["timestamp"]).dt.tz_localize(None)

            self._cache[key] = df
            self._time[key] = datetime.now()
            logger.info(f"[YF] OK {symbol} — {len(df)} bougies")
            return df

        except Exception as e:
            logger.error(f"[YF] Erreur {symbol}: {e}")
            return None

    def get_price(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Prix actuel + change 24h approximatif"""
        df = self.get_ohlcv(symbol, period="5d", interval="1h")
        if df is None or df.empty:
            return None

        last = df.iloc[-1]
        first = df.iloc[0]
        change = ((last["close"] - first["close"]) / first["close"] * 100) if first["close"] else 0

        return {
            "symbol": symbol,
            "price": round(float(last["close"]), 5),
            "timestamp": last["timestamp"].isoformat(),
            "change_24h_pct": round(change, 4),
            "high_24h": round(float(df["high"].max()), 5),
            "low_24h": round(float(df["low"].min()), 5),
            "volume": int(df["volume"].sum()),
            "source": "yahoo_fallback",
        }

    def clear_cache(self):
        self._cache.clear()
        self._time.clear()


# Instance singleton
yf_fallback = YahooFallback()


def get_price_with_fallback(
    symbol: str,
    primary_func=None
) -> Optional[Dict[str, Any]]:
    """
    Utilitaire : essaie la source principale, fallback YF si échec
    """
    if primary_func:
        try:
            data = primary_func(symbol)
            if data:
                return {**data, "source": "primary"}
        except Exception as e:
            logger.warning(f"[PRIMARY] Fail {symbol}: {e}")

    return yf_fallback.get_price(symbol)
