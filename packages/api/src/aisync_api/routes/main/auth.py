from fastapi import APIRouter

router = APIRouter(prefix="/auth")


@router.get("/signup")
async def signup():
    return {"message": "signup"}


@router.get("/signin")
async def login():
    return {"message": "signin"}
