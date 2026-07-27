import os,hashlib
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI,Request,HTTPException,UploadFile,File,Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from .market import klines
from .analysis_engine import analyze
from .storage import init_db,add_trade,rows,add_alert
from .vision import analyze_image
import httpx
app=FastAPI(title="Crypto Copilot IA"); app.add_middleware(SessionMiddleware,secret_key=os.getenv("SESSION_SECRET","change-me")); app.mount("/static",StaticFiles(directory="app/static"),name="static"); scheduler=AsyncIOScheduler()
def auth(r):
    if not r.session.get("ok"): raise HTTPException(401,"Connexion requise")
@app.on_event("startup")
async def start():
    init_db(); scheduler.add_job(scan,"interval",minutes=5,id="watch",replace_existing=True); scheduler.start()
@app.get("/",response_class=HTMLResponse)
async def home(): return Path("app/static/index.html").read_text()
@app.get("/api/me")
async def me(r:Request): return {"authenticated":bool(r.session.get("ok"))}
@app.post("/api/login")
async def login(r:Request):
    d=await r.json()
    if d.get("username")!=os.getenv("APP_USERNAME","pascaline") or d.get("password")!=os.getenv("APP_PASSWORD","change-moi"): raise HTTPException(401,"Identifiants incorrects")
    r.session["ok"]=True; return {"ok":True}
@app.post("/api/logout")
async def logout(r:Request): r.session.clear(); return {"ok":True}
@app.get("/api/analyze/{symbol}")
async def ana(symbol:str,r:Request,interval:str="15m"):
    auth(r); df=await klines(symbol,interval); out=analyze(df); out.update({"symbol":symbol.upper(),"interval":interval,"as_of":df.close_time.iloc[-1].isoformat()}); return out
@app.post("/api/screenshot")
async def shot(r:Request,file:UploadFile=File(...),question:str=Form("Analyse cette configuration")):
    auth(r); content=await file.read(); return {"analysis":analyze_image(content,file.content_type,question)}
@app.post("/api/trades")
async def trade(r:Request): auth(r); add_trade(await r.json()); return {"ok":True}
@app.get("/api/trades")
async def trades(r:Request): auth(r); return rows("SELECT * FROM trades ORDER BY id DESC LIMIT 200")
@app.get("/api/alerts")
async def alerts(r:Request): auth(r); return rows("SELECT * FROM alerts ORDER BY id DESC LIMIT 100")
async def notify(text):
    t=os.getenv("TELEGRAM_BOT_TOKEN",""); chat=os.getenv("TELEGRAM_CHAT_ID","")
    if t and chat:
        async with httpx.AsyncClient(timeout=15) as c: await c.post(f"https://api.telegram.org/bot{t}/sendMessage",json={"chat_id":chat,"text":text})
async def scan():
    syms=[x.strip().upper() for x in os.getenv("WATCHLIST","BTCUSDT,ETHUSDT,SOLUSDT").split(",") if x.strip()]; i=os.getenv("WATCH_INTERVAL","15m"); threshold=int(os.getenv("MIN_ALERT_SCORE","75"))
    for s in syms:
        try:
            df=await klines(s,i); out=analyze(df); fp=hashlib.sha256(f"{s}|{i}|{df.close_time.iloc[-1]}|{out['side']}".encode()).hexdigest()
            if out["confirmed"] and out["score"]>=threshold and add_alert(s,i,out,fp):
                msg = (f"🚨 {s} {i}\n{out['side']} confirmé — {out['score']} %\n"
                       f"Entrée {out['entry']:.6g} | Stop {out['stop']:.6g}\n"
                       f"TP1 {out['tp1']:.6g} | TP2 {out['tp2']:.6g} | TP3 {out['tp3']:.6g}")
                await notify(msg)
        except Exception: pass
@app.post("/api/scan-now")
async def now(r:Request): auth(r); await scan(); return {"ok":True}
