import json

from fastapi import APIRouter, Cookie, HTTPException

from app.services.analysis_engine import analyze
from app.services.auth import get_user
from app.services.database import connect

router = APIRouter(tags=["analysis"])


@router.get("/analyze/{symbol}")
async def run_analysis(symbol: str, session: str | None = Cookie(default=None)):
    user = get_user(session)
    if not user:
        raise HTTPException(401, "Connexion requise.")
    try:
        result = await analyze(symbol)
    except ValueError as e:
        raise HTTPException(400, str(e))
    with connect() as db:
        db.execute(
            "INSERT INTO analyses(user_id,symbol,signal,confidence,result_json) VALUES(?,?,?,?,?)",
            (user["id"], result["symbol"], result["signal"], result["confidence"], json.dumps(result)),
        )
        db.commit()
    return result


@router.get("/history")
async def history(session: str | None = Cookie(default=None)):
    user = get_user(session)
    if not user:
        raise HTTPException(401, "Connexion requise.")
    with connect() as db:
        rows = db.execute(
            "SELECT id,symbol,signal,confidence,created_at FROM analyses WHERE user_id=? ORDER BY id DESC LIMIT 20",
            (user["id"],),
        ).fetchall()
    return [dict(r) for r in rows]
