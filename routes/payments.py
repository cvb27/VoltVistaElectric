from fastapi import APIRouter

router = APIRouter(prefix="/payments", tags=["payments"])

@router.get("")
def payments_page():
    return {"ok": True}