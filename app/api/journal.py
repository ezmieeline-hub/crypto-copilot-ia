from fastapi import APIRouter, Cookie, HTTPException
from pydantic import BaseModel

from app.services.auth import get_user
from app.services.database import connect

router = APIRouter(tags=["journal"])


class JournalBody(BaseModel):
    taken: bool
    result_percent: float | None = None
    comment: str = ""


@router.post("/journal/{analysis_id}")
async def create_journal_entry(
    analysis_id: int,
    body: JournalBody,
    session: str | None = Cookie(default=None),
):
    user = get_user(session)
    if not user:
        raise HTTPException(401, "Connexion requise.")

    with connect() as db:
        analysis = db.execute(
            "SELECT symbol FROM analyses WHERE id=? AND user_id=?",
            (analysis_id, user["id"]),
        ).fetchone()

        if not analysis:
            raise HTTPException(404, "Analyse introuvable.")

        db.execute(
            """INSERT INTO journal(user_id,analysis_id,symbol,taken,result_percent,comment)
               VALUES(?,?,?,?,?,?)""",
            (
                user["id"],
                analysis_id,
                analysis["symbol"],
                body.taken,
                body.result_percent,
                body.comment,
            ),
        )
        db.commit()

    return {"ok": True}


@router.get("/journal")
async def list_journal(session: str | None = Cookie(default=None)):
    user = get_user(session)
    if not user:
        raise HTTPException(401, "Connexion requise.")

    with connect() as db:
        rows = db.execute(
            """SELECT id,symbol,taken,result_percent,comment,created_at
               FROM journal WHERE user_id=? ORDER BY id DESC LIMIT 50""",
            (user["id"],),
        ).fetchall()

    return [dict(r) for r in rows]
