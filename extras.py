from fastapi import APIRouter, Cookie, File, HTTPException, UploadFile
from app.services.auth import get_user
from app.services.database import connect

router=APIRouter(tags=["extras"])

@router.post("/tradingview/analyze")
async def tradingview(file: UploadFile=File(...), session: str|None=Cookie(default=None)):
    user=get_user(session)
    if not user: raise HTTPException(401,"Connexion requise.")
    if not (file.content_type or "").startswith("image/"): raise HTTPException(400,"Le fichier doit être une image.")
    data=await file.read()
    if len(data)>8_000_000: raise HTTPException(400,"Image trop volumineuse.")
    return {"ok":True,"filename":file.filename,"summary":"Capture reçue. Tendance visuelle neutre à confirmer avec les indicateurs.","signal":"ATTENDRE"}

@router.get("/alerts")
async def alerts(session: str|None=Cookie(default=None)):
    user=get_user(session)
    if not user: raise HTTPException(401,"Connexion requise.")
    with connect() as db:
        rows=db.execute("SELECT id,symbol,target_price,direction,active FROM alerts WHERE user_id=? ORDER BY id DESC",(user["id"],)).fetchall()
    return [dict(r) for r in rows]

@router.post("/alerts/{symbol}/{direction}/{target_price}")
async def create_alert(symbol:str,direction:str,target_price:float,session:str|None=Cookie(default=None)):
    user=get_user(session)
    if not user: raise HTTPException(401,"Connexion requise.")
    if direction not in {"above","below"}: raise HTTPException(400,"Direction invalide.")
    with connect() as db:
        db.execute("INSERT INTO alerts(user_id,symbol,target_price,direction,active) VALUES(?,?,?,?,1)",(user["id"],symbol.upper(),target_price,direction))
        db.commit()
    return {"ok":True}
