from pydantic import BaseModel


class BookIn(BaseModel):
    title: str
    rating: float
    completed: bool

    class Config:
        orm_mode = True


class Book(BaseModel):
    id:  int
    title: str
    rating: float
    completed: bool

    class Config:
        orm_mode = True


class AuthorIn(BaseModel):
    name: str
    age: int

    class Config:
        orm_mode = True


class Author(BaseModel):
    id: int
    name: str
    age: int

    class Config:
        orm_mode = True
