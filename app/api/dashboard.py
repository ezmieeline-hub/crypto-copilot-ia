from collections import defaultdict

from fastapi import APIRouter, Cookie, HTTPException

from app.services.auth import get_user
from app.services.database import connect

router = APIRouter(tags=["dashboard"])


def _period_key(value, length):
    if hasattr(value, "strftime"):
        return value.strftime("%Y-%m") if length == 7 else value.strftime("%Y-%m-%d")
    return str(value)[:length]


@router.get("/dashboard")
async def dashboard(session: str | None = Cookie(default=None)):
    user = get_user(session)
    if not user:
        raise HTTPException(401, "Connexion requise.")

    with connect() as db:
        analyses = db.execute(
            "SELECT id,symbol,confidence,created_at FROM analyses WHERE user_id=?",
            (user["id"],),
        ).fetchall()

        journal = db.execute(
            "SELECT symbol,taken,result_percent,created_at FROM journal WHERE user_id=?",
            (user["id"],),
        ).fetchall()

    total_analyses = len(analyses)

    avg_score = (
        round(sum(a["confidence"] for a in analyses) / total_analyses, 1)
        if total_analyses
        else 0
    )

    taken_trades = [
        j for j in journal if j["taken"] and j["result_percent"] is not None
    ]
    total_taken = len(taken_trades)

    wins = [j for j in taken_trades if j["result_percent"] > 0]
    success_rate = (
        round((len(wins) / total_taken) * 100, 1) if total_taken else 0
    )

    cumulative_gain = round(sum(j["result_percent"] for j in taken_trades), 2)

    by_symbol = defaultdict(float)
    for j in taken_trades:
        by_symbol[j["symbol"]] += j["result_percent"]

    best_symbol = max(by_symbol, key=by_symbol.get) if by_symbol else None
    worst_symbol = min(by_symbol, key=by_symbol.get) if by_symbol else None

    by_month = defaultdict(float)
    for j in taken_trades:
        month = _period_key(j["created_at"], 7)
        by_month[month] += j["result_percent"]

    best_month = max(by_month, key=by_month.get) if by_month else None

    by_day = defaultdict(int)
    for a in analyses:
        day = _period_key(a["created_at"], 10)
        by_day[day] += 1

    avg_per_day = (
        round(total_analyses / len(by_day), 1) if by_day else 0
    )

    return {
        "total_analyses": total_analyses,
        "success_rate": success_rate,
        "cumulative_gain": cumulative_gain,
        "best_symbol": best_symbol,
        "worst_symbol": worst_symbol,
        "avg_score": avg_score,
        "best_month": best_month,
        "avg_analyses_per_day": avg_per_day,
    }
