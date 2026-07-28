from fastapi import APIRouter, Cookie, HTTPException, Response
from pydantic import BaseModel
from app.services.auth import register_user, login_user, get_user

router = APIRouter(tags=["auth"])

class RegisterBody(BaseModel):
    name: str
    email: str
    password: str

class LoginBody(BaseModel):
    email: str
    password: str

@router.post("/register")
async def register(body: RegisterBody):
    if len(body.password) < 6:
        raise HTTPException(400, "Le mot de passe doit contenir au moins 6 caractères.")
    try:
        register_user(body.name, body.email, body.password)
        return {"ok": True}
    except Exception:
        raise HTTPException(409, "Cette adresse e-mail existe déjà.")

@router.post("/login")
async def login(body: LoginBody, response: Response):
    result = login_user(body.email, body.password)
    if not result:
        raise HTTPException(401, "Identifiants incorrects.")
    token, user = result
    response.set_cookie("session", token, httponly=True, samesite="lax", max_age=86400 * 30)
    return {"ok": True, "user": user}

@router.get("/me")
async def me(session: str | None = Cookie(default=None)):
    user = get_user(session)
    if not user:
        raise HTTPException(401, "Connexion requise.")
    return user

@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("session")
    return {"ok": True}
