import json

from fastapi import (
    APIRouter,
    Cookie,
    HTTPException,
)

from app.services.analysis_engine import analyze
from app.services.auth import get_user
from app.services.database import connect

router = APIRouter(
    tags=["analysis"]
)


# ==========================================================
# ANALYSE
# ==========================================================

@router.get("/analyze/{symbol}")

async def run_analysis(

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

        result = await analyze(

            symbol=symbol,

        )

    except ValueError as exc:

        raise HTTPException(

            status_code=400,

            detail=str(exc),

        )

    except Exception as exc:

        raise HTTPException(

            status_code=500,

            detail=str(exc),

        )

    with connect() as db:

        db.execute(

            """
            INSERT INTO analyses(

                user_id,
                symbol,
                signal,
                confidence,
                result_json

            )

            VALUES(

                ?,
                ?,
                ?,
                ?,
                ?

            )
            """,

            (

                user["id"],

                result.get(
                    "symbol",
                    symbol.upper(),
                ),

                result.get(
                    "signal",
                    "ATTENDRE",
                ),

                result.get(
                    "confidence",
                    0,
                ),

                json.dumps(result),

            ),

        )

        db.commit()

    return result


# ==========================================================
# HISTORIQUE
# ==========================================================

@router.get("/history")

async def history(

    session: str | None = Cookie(default=None),

):

    user = get_user(session)

    if not user:

        raise HTTPException(

            status_code=401,

            detail="Connexion requise.",

        )

    with connect() as db:

        rows = db.execute(

            """
            SELECT

                id,
                symbol,
                signal,
                confidence,
                created_at

            FROM analyses

            WHERE user_id=?

            ORDER BY id DESC

            LIMIT 20
            """,

            (

                user["id"],

            ),

        ).fetchall()

    return [

        dict(row)

        for row in rows

    ]
