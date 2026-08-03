import httpx

CRYPTOPANIC_URL = "https://cryptopanic.com/api/v1/posts/"
FOREXFACTORY_URL = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"


async def get_crypto_news(symbol: str, api_key: str, limit: int = 5):
    if not api_key:
        return []

    params = {
        "auth_token": api_key,
        "currencies": symbol.upper(),
        "public": "true",
    }

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(CRYPTOPANIC_URL, params=params)
            r.raise_for_status()
            data = r.json()
    except Exception:
        return []

    news = []
    for item in data.get("results", [])[:limit]:
        news.append(
            {
                "title": item.get("title"),
                "source": (item.get("source") or {}).get("title"),
                "published_at": item.get("published_at"),
                "url": item.get("url"),
            }
        )
    return news


async def get_economic_calendar(limit: int = 5):
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(FOREXFACTORY_URL)
            r.raise_for_status()
            data = r.json()
    except Exception:
        return []

    high_impact = [
        {
            "title": e.get("title"),
            "country": e.get("country"),
            "date": e.get("date"),
            "impact": e.get("impact"),
            "forecast": e.get("forecast"),
            "previous": e.get("previous"),
        }
        for e in data
        if e.get("impact") == "High" and e.get("country") == "USD"
    ]
    return high_impact[:limit]
