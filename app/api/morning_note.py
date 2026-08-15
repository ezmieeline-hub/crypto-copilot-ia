import json

from fastapi import APIRouter, Cookie, HTTPException

from app.services.morning_note import generate_morning_note_for_symbol
from app.services.auth import get_user
from app.services.database import connect

router = APIRouter(tags=["morning-note"])


# ==========================================================
# MORNING NOTE
# ==========================================================

@router.get("/morning-note/{symbol}")
async def morning_note(
    symbol: str,
    session: str | None = Cookie(default=None),
):
    user = get_user(session)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Connexion requise.",
        )

    try:
        result = await generate_morning_note_for_symbol(symbol)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    # Sauvegarde en base
    with connect() as db:
        cursor = db.execute(
            """
            INSERT INTO analyses(
                user_id,
                symbol,
                signal,
                confidence,
                result_json
            )
            VALUES(?, ?, ?, ?, ?)
            RETURNING id
            """,
            (
                user["id"],
                result.get("symbol", symbol.upper()),
                result.get("bias", "BASE"),
                int(result.get("bias_scores", {}).get("bull", 0)),
                json.dumps(result),
            ),
        )
        new_id = cursor.fetchone()["id"]
        db.commit()

    result["analysis_id"] = new_id
    return result
