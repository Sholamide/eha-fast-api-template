import uvicorn
from fastapi import FastAPI, status, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
# from schemas import User as SchemaUser, UserIn as SchemaUserIn, UserInDB, TechTalk as SchemaTechTalk, TechTalkIn as SchemaTechTalkIn, TokenData, Token
from schemas import User, UserCreate, UserInDB, UserUpdate
from schemas import TechTalk, TechTalkCreate, TechTalkInDB, TechTalkUpdate, Token, TokenData
from typing import List
import sqlalchemy
from sqlalchemy import create_engine, Table, Column, DateTime, Integer, String, Boolean
import databases
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.sql import func
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from passlib.context import CryptContext
from jose import JWTError, jwt

load_dotenv('.env')

# authentication
SECRET_KEY = "1cca70da0fe469cfe8552f36921729988c6a887d3f02c67d4318b8f1a2443650"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# fake user database
dummy_db = {
    "johndoe": {
        "id": "1",
        "username": "johndoe",
        "full_name": "John Doe",
        "email": "johndoe@example.com",
        "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
        "disabled": False,
        "is_active": True,
        "is_superuser": False
    }
}

database = databases.Database(os.environ.get('DATABASE_URI'))
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

metadata = sqlalchemy.MetaData()

techtalks = Table(
    "techtalks",
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("title", String),
    Column("description", String),
    Column("thumbsup", Integer),
    Column("timeoftalk", DateTime(timezone=True), server_default=func.now()),
    Column("completed", Boolean, default=False),
    Column("time_created", DateTime(timezone=True), server_default=func.now()),
    Column("time_updated", DateTime(timezone=True), onupdate=func.now()),
)

users = Table(
    "users",
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("username", String, index=True),
    Column("full_name", String, index=True),
    Column("email", String, unique=True, index=True, nullable=False),
    Column("hashed_password", String, nullable=False),
    Column("is_active", Boolean, default=False),
    Column("is_superuser", Boolean, default=False),
    Column("time_created", DateTime(timezone=True), server_default=func.now()),
    Column("time_updated", DateTime(timezone=True), onupdate=func.now()),
)

engine = create_engine(
    os.environ.get('DATABASE_URI'), pool_size=3, max_overflow=0
)
metadata.create_all(engine)


app = FastAPI(title="FASTAPI library project spike demonstration")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def get_user(db, username: str):
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)


def authenticate_user(fake_db, username: str, password: str):
    user = get_user(fake_db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user(dummy_db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user
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

# requests for the JWT authentication
# post request that generates a token


@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(
        dummy_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@ app.post('/techtalks/', response_model=TechTalk, status_code=status.HTTP_201_CREATED)
async def create_techtalk(techtalk: TechTalkCreate):
    query = techtalks.insert().values(title=techtalk.title, description=techtalk.description,
                                      thumbsup=techtalk.thumbsup, completed=techtalk.completed)
    last_record_id = await database.execute(query)
    return {**techtalk.dict(), "id": last_record_id}


@app.post('/users/', response_model=User, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate):
    query = users.insert().values(full_name=user.full_name, email=user.email,
                                  is_active=user.is_active, is_superuser=user.is_superuser)
    last_record_id = await database.execute(query)
    return {**user.dict(), "id": last_record_id}


@app.get('/techtalks/', response_model=List[TechTalk], status_code=status.HTTP_200_OK)
async def get_techtalks(skip: int = 0, take: int = 100):
    query = techtalks.select().offset(skip).limit(take)
    return await database.fetch_all(query)


@app.get('/users/', response_model=List[User], status_code=status.HTTP_200_OK)
async def get_users(skip: int = 0, take: int = 100):
    query = users.select().offset(skip).limit(take)
    return await database.fetch_all(query)


@app.put("/techtalks/{techtalk_id}/", response_model=TechTalk, status_code=status.HTTP_200_OK)
async def update_techtalk(techtalk_id: int, payload: TechTalkUpdate):
    query = techtalks.update().where(techtalks.c.id == techtalk_id).values(
        title=payload.title, description=payload.description,
        thumbsup=payload.thumbsup, completed=payload.completed)
    await database.execute(query)
    return {**payload.dict(), "id": techtalk_id}


@app.put("/users/{user_id}/", response_model=User, status_code=status.HTTP_200_OK)
async def update_user(user_id: int, payload: UserUpdate):
    query = users.update().where(users.c.id == user_id).values(
        username=payload.username, full_name=payload.full_name, email=payload.full_name)
    await database.execute(query)
    return {**payload.dict(), "id": user_id}


@app.get("/techtalks/{techtalk_id}/", response_model=TechTalk, status_code=status.HTTP_200_OK)
async def getBookByID(techtalk_id: int):
    query = techtalks.select().where(techtalks.c.id == techtalk_id)
    return await database.fetch_one(query)


@app.get("/users/{user_id}/", response_model=User, status_code=status.HTTP_200_OK)
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


@app.get("/users/me/", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user


@app.get("/users/me/items/")
async def read_own_items(current_user: User = Depends(get_current_active_user)):
    return [{"item_id": "Foo", "owner": current_user.username}]

# To run locally
if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8000)
