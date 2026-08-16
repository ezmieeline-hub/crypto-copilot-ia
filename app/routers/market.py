from fastapi import APIRouter, HTTPException, Query
from typing import Literal
from app.providers.yahoo_fallback import yf_fallback

router = APIRouter(prefix="/market", tags=["market"])


@router.get("/price/{symbol}")
async def price(
    symbol: str,
    source: Literal["auto", "yahoo"] = "auto"
):
    """
    Prix actuel d'un actif.
    Ex: XAUUSD, EURUSD, AAPL, BTCUSD
    """
    data = yf_fallback.get_price(symbol)
    if not data:
        raise HTTPException(404, f"Données indisponibles pour {symbol}")
    return data


@router.get("/ohlcv/{symbol}")
async def ohlcv(
    symbol: str,
    period: str = Query("1mo", regex="^(1d|5d|1mo|3mo|6mo|1y|2y|5y|10y|ytd|max)$"),
    interval: str = Query("1h", regex="^(1m|2m|5m|15m|30m|60m|90m|1h|1d|5d|1wk|1mo|3mo)$")
):
    """
    Historique OHLCV complet.
    Ex: /market/ohlcv/XAUUSD?period=1mo&interval=1h
    """
    df = yf_fallback.get_ohlcv(symbol, period, interval)
    if df is None:
        raise HTTPException(404, f"Pas de données pour {symbol}")
    return df.to_dict(orient="records")


@router.post("/cache/clear")
async def clear_cache():
    """Vide le cache manuellement"""
    yf_fallback.clear_cache()
    return {"status": "cache_cleared"}
