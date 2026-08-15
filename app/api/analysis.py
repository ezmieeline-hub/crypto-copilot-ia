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
        raise HTTPException(status_code=401, detail="Connexion requise.")
    try:
        result = await analyze(symbol=symbol)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    with connect() as db:
        cursor = db.execute(
            """INSERT INTO analyses(user_id, symbol, signal, confidence, result_json)
               VALUES(?, ?, ?, ?, ?) RETURNING id""",
            (
                user["id"],
                result.get("symbol", symbol.upper()),
                result.get("signal", "ATTENDRE"),
                result.get("confidence", 0),
                json.dumps(result),
            ),
        )
        new_id = cursor.fetchone()["id"]
        db.commit()

    result["analysis_id"] = new_id
    return result


@router.get("/history")
async def history(session: str | None = Cookie(default=None)):
    user = get_user(session)
    if not user:
        raise HTTPException(status_code=401, detail="Connexion requise.")
    with connect() as db:
        rows = db.execute(
            """SELECT id, symbol, signal, confidence, created_at
               FROM analyses WHERE user_id=? ORDER BY id DESC LIMIT 20""",
            (user["id"],),
        ).fetchall()
    return [dict(row) for row in rows]


@router.get("/history/{analysis_id}")
async def get_analysis_by_id(analysis_id: int, session: str | None = Cookie(default=None)):
    user = get_user(session)
    if not user:
        raise HTTPException(status_code=401, detail="Connexion requise.")
    with connect() as db:
        row = db.execute(
            "SELECT result_json FROM analyses WHERE id=? AND user_id=?",
            (analysis_id, user["id"]),
        ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Analyse non trouvée.")
    return json.loads(row["result_json"])


@router.delete("/history")
async def clear_history(session: str | None = Cookie(default=None)):
    user = get_user(session)
    if not user:
        raise HTTPException(status_code=401, detail="Connexion requise.")
    with connect() as db:
        db.execute("DELETE FROM analyses WHERE user_id=?", (user["id"],))
        db.commit()
    return {"ok": True, "message": "Historique supprimé."}
