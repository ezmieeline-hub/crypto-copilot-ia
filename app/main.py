from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.core.config import STATIC_DIR, TEMPLATES_DIR
from app.services.database import init_db
from app.api.health import router as health_router
from app.api.auth import router as auth_router
from app.api.analysis import router as analysis_router
from app.api.extras import router as extras_router
from app.api.journal import router as journal_router
from app.api.dashboard import router as dashboard_router
from app.api.compare import router as compare_router
from app.api.morning_note import router as morning_note_router

app = FastAPI(title="Crypto Copilot IA V5", version="5.0.0")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

for router in (
    health_router,
    auth_router,
    analysis_router,
    extras_router,
    journal_router,
    dashboard_router,
    compare_router,
    morning_note_router,
):
    app.include_router(router, prefix="/api")

@app.on_event("startup")
def startup():
    init_db()

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
