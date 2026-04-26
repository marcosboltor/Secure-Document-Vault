from fastapi import APIRouter

router = APIRouter(prefix="/users", tags=["Personnel"])

@router.get("/")
async def list_users():
    return []

@router.post("/")
async def register_user():
    return {"message": "User registration endpoint"}
