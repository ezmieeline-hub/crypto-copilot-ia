import httpx, pandas as pd
BASE="https://api.binance.com"
ALLOWED={"1m","3m","5m","15m","30m","1h","2h","4h","6h","8h","12h","1d"}
async def klines(symbol,interval="15m",limit=500):
    symbol=symbol.upper().replace("/","")
    if interval not in ALLOWED: raise ValueError("Unité non prise en charge")
    async with httpx.AsyncClient(timeout=20) as c:
        r=await c.get(f"{BASE}/api/v3/klines",params={"symbol":symbol,"interval":interval,"limit":limit}); r.raise_for_status()
    cols=["open_time","open","high","low","close","volume","close_time","quote_volume","trades","taker_base","taker_quote","ignore"]
    df=pd.DataFrame(r.json(),columns=cols)
    for x in ["open","high","low","close","volume","quote_volume"]: df[x]=pd.to_numeric(df[x],errors="coerce")
    df["open_time"]=pd.to_datetime(df["open_time"],unit="ms",utc=True); df["close_time"]=pd.to_datetime(df["close_time"],unit="ms",utc=True)
    return df
