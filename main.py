import uvicorn
from fastapi import FastAPI, status, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from schema import TechTalk as SchemaTechTalk, TechTalkIn as SchemaTechTalkIn
from schema import User as SchemaUser, UserIn as SchemaUserIn
from typing import List
import sqlalchemy
from sqlalchemy import create_engine, Table, Column, DateTime, Integer, String, Boolean
import databases

from sqlalchemy.sql import func
import os
from dotenv import load_dotenv
load_dotenv('.env')

# authentication
SECRET_KEY = "ad73cd8d456a79cde5174bf21b06a368e85706f2ccc1ea7af18d4538d5ab5eb8"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# fake user database
fake_users_db = {
    "johndoe": {
        "username": "johndoe",
        "full_name": "John Doe",
        "email": "johndoe@example.com",
        "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
        "disabled": False,
    }
}

database = databases.Database(os.environ.get('DATABASE_URI'))

metadata = sqlalchemy.MetaData()

techtalks = Table(
    "techtalks",
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("title", String),
    Column("description", String),
    Column("thumbsup", Integer),
    Column("completed", Boolean, default=False),
    Column("time_created", DateTime(timezone=True), server_default=func.now()),
    Column("time_updated", DateTime(timezone=True), onupdate=func.now()),

)

users = Table(
    "users",
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("full_name", String, index=True),
    Column("email", String, unique=True, index=True, nullable=False),
    Column("hashed_password", String, nullable=False),
    Column("is_active", Boolean, default=True),
    Column("is_superuser", Boolean, default=False),
    Column("time_created", DateTime(timezone=True), server_default=func.now()),
    Column("time_updated", DateTime(timezone=True), onupdate=func.now()),
)

engine = create_engine(
    os.environ.get('DATABASE_URI'), pool_size=3, max_overflow=0
)
metadata.create_all(engine)

app = FastAPI(title="EHA FASTAPI library project demonstration")

# to avoid csrftokenError
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


@app.on_event("startup")
async def startup():
    await database.connect()


@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()


@ app.get("/")
async def root():
    return {"message": "Not Found"}


@ app.post('/techtalks/', response_model=SchemaTechTalk, status_code=status.HTTP_201_CREATED)
async def create_techtalk(techtalk: SchemaTechTalkIn):
    query = techtalks.insert().values(title=techtalk.title, description=techtalk.description,
                                      thumbsup=techtalk.thumbsup, completed=techtalk.completed)
    last_record_id = await database.execute(query)
    return {**techtalk.dict(), "id": last_record_id}


@app.post('/users/', response_model=SchemaUser, status_code=status.HTTP_201_CREATED)
async def create_user(user: SchemaUserIn):
    query = users.insert().values(full_name=user.full_name, email=user.email,
                                  is_active=user.is_active, is_superuser=user.is_superuser)
    last_record_id = await database.execute(query)
    return {**user.dict(), "id": last_record_id}


@app.get('/techtalks/', response_model=List[SchemaTechTalk], status_code=status.HTTP_200_OK)
async def get_techtalks(skip: int = 0, take: int = 100):
    query = techtalks.select().offset(skip).limit(take)
    return await database.fetch_all(query)


@app.get('/users/', response_model=List[SchemaUser], status_code=status.HTTP_200_OK)
async def get_users(skip: int = 0, take: int = 100):
    query = users.select().offset(skip).limit(take)
    return await database.fetch_all(query)


@app.put("/techtalks/{techtalk_id}/", response_model=SchemaTechTalk, status_code=status.HTTP_200_OK)
async def update_techtalk(techtalk_id: int, payload: SchemaTechTalkIn):
    query = techtalks.update().where(techtalks.c.id == techtalk_id).values(
        title=payload.title, description=payload.description,
        thumbsup=payload.thumbsup, completed=payload.completed)
    await database.execute(query)
    return {**payload.dict(), "id": techtalk_id}


@app.put("/users/{user_id}/", response_model=SchemaUser, status_code=status.HTTP_200_OK)
async def update_user(user_id: int, payload: SchemaUserIn):
    query = users.update().where(users.c.id == user_id).values(
        name=payload.name, age=payload.age)
    await database.execute(query)
    return {**payload.dict(), "id": user_id}


@app.get("/techtalks/{techtalk_id}/", response_model=SchemaTechTalk, status_code=status.HTTP_200_OK)
async def getBookByID(techtalk_id: int):
    query = techtalks.select().where(techtalks.c.id == techtalk_id)
    return await database.fetch_one(query)


@app.get("/users/{user_id}/", response_model=SchemaUser, status_code=status.HTTP_200_OK)
async def getBookByID(user_id: int):
    query = users.select().where(users.c.id == user_id)
    return await database.fetch_one(query)


@app.delete("/techtalks/{techtalk_id}/", status_code=status.HTTP_200_OK)
async def delete_techtalk(techtalk_id: int):
    query = techtalks.delete().where(techtalks.c.id == techtalk_id)
    await database.execute(query)
    return {"message": "Tech Talk with id: {} deleted successfully!".format(techtalk_id)}


@app.delete("/users/{user_id}/", status_code=status.HTTP_200_OK)
async def update_note(user_id: int):
    query = users.delete().where(users.c.id == user_id)
    await database.execute(query)
    return {"message": "user with id: {} deleted successfully!".format(user_id)}


# To run locally
if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8000)
