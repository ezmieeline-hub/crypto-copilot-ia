from fastapi import APIRouter

router = APIRouter(tags=["system"])

@router.get("/health")
async def health():
    return {"status": "ok", "application": "Crypto Copilot IA", "version": "5.0.0"}
