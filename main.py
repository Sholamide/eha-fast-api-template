import uvicorn
from fastapi import FastAPI, status, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from schema import Book as SchemaBook, BookIn as SchemaBookIn
from schema import Author as SchemaAuthor, AuthorIn as SchemaAuthorIn
from typing import List
import sqlalchemy
from sqlalchemy import create_engine, Table, Column, DateTime, ForeignKey, Integer, String, Float, Boolean
from schema import Book
from schema import Author
import databases
from models import Book as ModelBook
from models import Author as ModelAuthor
from sqlalchemy.sql import func
import os
from dotenv import load_dotenv
from sqlalchemy.orm import relationship
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

books = sqlalchemy.Table(
    "books",
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("title", String),
    Column("rating", Float),
    Column("completed", Boolean),
    Column("time_created", DateTime(timezone=True), server_default=func.now()),
    Column("time_updated", DateTime(timezone=True), onupdate=func.now()),
)

authors = sqlalchemy.Table(
    "authors",
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("name", String),
    Column("age", Integer),
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


@ app.post('/books/', response_model=SchemaBook, status_code=status.HTTP_201_CREATED)
async def create_book(book: SchemaBookIn):
    query = books.insert().values(title=book.title, rating=book.rating,
                                  completed=book.completed)
    last_record_id = await database.execute(query)
    return {**book.dict(), "id": last_record_id}


@app.post('/authors/', response_model=SchemaAuthor, status_code=status.HTTP_201_CREATED)
async def create_author(author: SchemaAuthorIn):
    query = authors.insert().values(name=author.name, age=author.age)
    last_record_id = await database.execute(query)
    return {**author.dict(), "id": last_record_id}


@app.get('/books/', response_model=List[SchemaBook], status_code=status.HTTP_200_OK)
async def get_books(skip: int = 0, take: int = 100):
    query = books.select().offset(skip).limit(take)
    return await database.fetch_all(query)


@app.get('/authors/', response_model=List[SchemaAuthor], status_code=status.HTTP_200_OK)
async def get_authors(skip: int = 0, take: int = 100):
    query = authors.select().offset(skip).limit(take)
    return await database.fetch_all(query)


@app.put("/books/{book_id}/", response_model=SchemaBook, status_code=status.HTTP_200_OK)
async def update_book(book_id: int, payload: SchemaBookIn):
    query = books.update().where(books.c.id == book_id).values(
        title=payload.title, rating=payload.rating, completed=payload.completed)
    await database.execute(query)
    return {**payload.dict(), "id": book_id}


@app.put("/authors/{author_id}/", response_model=SchemaAuthor, status_code=status.HTTP_200_OK)
async def update_author(author_id: int, payload: SchemaAuthorIn):
    query = authors.update().where(authors.c.id == author_id).values(
        name=payload.name, age=payload.age)
    await database.execute(query)
    return {**payload.dict(), "id": author_id}


@app.get("/books/{book_id}/", response_model=SchemaBook, status_code=status.HTTP_200_OK)
async def getBookByID(book_id: int):
    query = books.select().where(books.c.id == book_id)
    return await database.fetch_one(query)


@app.get("/authors/{author_id}/", response_model=SchemaAuthor, status_code=status.HTTP_200_OK)
async def getBookByID(author_id: int):
    query = authors.select().where(authors.c.id == author_id)
    return await database.fetch_one(query)


@app.delete("/books/{book_id}/", status_code=status.HTTP_200_OK)
async def delete_book(book_id: int):
    query = books.delete().where(books.c.id == book_id)
    await database.execute(query)
    return {"message": "Book with id: {} deleted successfully!".format(book_id)}


@app.delete("/authors/{author_id}/", status_code=status.HTTP_200_OK)
async def update_note(author_id: int):
    query = authors.delete().where(authors.c.id == author_id)
    await database.execute(query)
    return {"message": "Author with id: {} deleted successfully!".format(author_id)}


# To run locally
if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8000)
