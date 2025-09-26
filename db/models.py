from sqlmodel import Field, SQLModel, Relationship
from pydantic import BaseModel

class Set(SQLModel, table = True):
    id: int | None = Field(default = None, primary_key = True)
    name: str
    cards: list["Card"] = Relationship(back_populates = "set")

class Card(SQLModel, table = True):
    id:int | None = Field(default = None, primary_key = True)
    question:str

    answer:str
    set_id: int | None = Field(default = None, foreign_key = "set.id")
    set: Set | None = Relationship(back_populates = "cards")
    incorrect_guesses: int

class User(BaseModel):
    id: int
    name: str
    email: str
    set_id: int