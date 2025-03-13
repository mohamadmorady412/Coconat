from fastapi import FastAPI, Depends

from ifpd import ifpd
ifpd()

from database import get_db
from models import User
from crud import CRUDBase
from sqlalchemy.ext.asyncio import AsyncSession

app = FastAPI()
user_crud = CRUDBase(User)

@app.get("/users/{user_id}")
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    return await user_crud.get(db, user_id)

@app.post("/users/")
async def create_user(user_data: dict, db: AsyncSession = Depends(get_db)):
    return await user_crud.create(db, user_data)
