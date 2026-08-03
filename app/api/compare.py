import json

from fastapi import APIRouter, Cookie, HTTPException

from app.services.auth import get_user
from app.services.database import connect

router = APIRouter(tags=["compare"])


@router.get("/compare/{symbol}")
async def compare(symbol: str, session: str | None = Cookie(default=None)):
    user = get_user(session)
    if not user:
        raise HTTPException(401, "Connexion requise.")

    with connect() as db:
        rows = db.execute(
            """SELECT confidence,result_json,created_at
               FROM analyses WHERE user_id=? AND symbol=?
               ORDER BY id DESC LIMIT 2""",
            (user["id"], symbol.upper()),
        ).fetchall()

    if len(rows) < 2:
        return {
            "available": False,
            "message": "Pas encore assez d'historique pour comparer.",
        }

    today, previous = rows[0], rows[1]

    today_data = json.loads(today["result_json"])
    previous_data = json.loads(previous["result_json"])

    today_market = today_data.get("market", {})
    previous_market = previous_data.get("market", {})

    today_bos = (
        today_data.get("analysis", {})
        .get("vision", {})
        .get("market_structure", {})
        .get("bos", False)
    )
    previous_bos = (
        previous_data.get("analysis", {})
        .get("vision", {})
        .get("market_structure", {})
        .get("bos", False)
    )

    changes = []

    delta_confidence = round(today["confidence"] - previous["confidence"], 1)

    rv_today = today_market.get("relative_volume")
    rv_prev = previous_market.get("relative_volume")
    if rv_today is not None and rv_prev is not None:
        if rv_today > rv_prev:
            changes.append("Le volume est meilleur.")
        elif rv_today < rv_prev:
            changes.append("Le volume est moins bon.")

    if today_bos and not previous_bos:
        changes.append("Un BOS est apparu.")
    elif not today_bos and previous_bos:
        changes.append("Le BOS a disparu.")

    rsi_today = today_market.get("rsi")
    rsi_prev = previous_market.get("rsi")
    if rsi_today is not None and rsi_prev is not None:
        if rsi_today > rsi_prev:
            changes.append("Le RSI progresse.")
        elif rsi_today < rsi_prev:
            changes.append("Le RSI recule.")

    adx_today = today_market.get("adx")
    adx_prev = previous_market.get("adx")
    if adx_today is not None and adx_prev is not None:
        if adx_today > adx_prev:
            changes.append("La tendance se renforce (ADX en hausse).")
        elif adx_today < adx_prev:
            changes.append("La tendance s'affaiblit (ADX en baisse).")

    return {
        "available": True,
        "symbol": symbol.upper(),
        "confidence_today": today["confidence"],
        "confidence_previous": previous["confidence"],
        "delta_confidence": delta_confidence,
        "changes": changes,
    }
