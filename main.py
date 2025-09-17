from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.templating import Jinja2Templates
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from db.session import create_db_and_tables, SessionDep
from sqlmodel import Session, Field, SQLModel, create_engine, select, Relationship
from random import randint

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load the DB
    create_db_and_tables()
    yield

app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory = "templates")

# groceryList = ["bread", "milk", "eggs", "ice cream", "more bread"]

class Set(SQLModel, table = True):
    id: int | None = Field(default = None, primary_key = True)
    name: str
    cards: list["Card"] = Relationship(back_populates = "set")
    # user_id: int

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

class Deck(BaseModel):
    id: int
    name: int

# setList = [
#     Set(id=1, name="Geography"),
#     Set(id=2, name="Animals"),
#     Set(id=3, name="Linguistics")
# ]

cardList = [Card(id = 1, question = "Where is Taylor University located?", answer = "Upland, IN, USA", set_id = 1, incorrect_guesses = 0),
            Card(id = 2, question = "What is the airspeed velocity of an unladen swallow?", answer = "~24 mph (European)", set_id = 2, incorrect_guesses = 0),
            Card(id = 3, question = "What is a group of cats called?", answer = "Clowder", set_id = 2, incorrect_guesses = 0),
            Card(id = 4, question = "What is the longest commonly accepted word in the English language?", answer = "Pneumonoultramicroscopicsilicovolcanoconiosis", set_id = 3, incorrect_guesses = 0),
            Card(id = 5, question = "In which U.S. state is it illegal to eat fried chicken with a fork?", answer = "Georgia", set_id = 1, incorrect_guesses = 0)]

userList = [User(id = 1, name = "Monty123", email = "caerbannog@gmail.com", set_id = 2),
            User(id = 2, name = "helpicantthinkofaname", email = "helpicantthinkofanemail@yahoo.com", set_id = 1)]

@app.get("/", response_class = HTMLResponse)
async def root(request:Request):
    return templates.TemplateResponse(request = request, name = "index.html", context = {"cards": cardList})

# @app.get("/items")
# async def getGroceryList():
#     return groceryList

@app.get("/cards")
async def getCards(q:str=""):
    searchResults = []
    for card in cardList:
        if q in card.question: searchResults.append(card)
    return searchResults

@app.get("/cards/{card_id}", name = "get_card", response_class = HTMLResponse)
async def getCardByID(card_id:int, request:Request):
    for card in cardList:
        if card.id == card_id: return templates.TemplateResponse(request = request, name = "card.html", context = {"card": cardList[card_id - 1]})
    return None

@app.get("/sets/{set_id}", name = "get_set", response_class = HTMLResponse)
async def getSetByID(session: SessionDep, set_id:int, request:Request):
    # for set in setList:
    #     if set.id == set_id: return templates.TemplateResponse(request = request, name = "set.html", context = {"set": cardList[card_id - 1]})
    # return None
    set = session.exec(select(Set).where(Set.id == set_id)).first()
    return templates.TemplateResponse(request=request, name="/set.html", context={"set":set})

@app.post("/sets/add")
async def create_set(session: SessionDep, set:Set):
    db_set = Set(name=set.name)
    session.add(db_set)
    session.commit()
    session.refresh(db_set)
    return db_set

@app.post("/card/add")
async def addCard(session: SessionDep, card:Card):
    # cardList.append(card)
    # return cardList
    db_card = Card(question=card.question, answer=card.answer, set_id=card.set_id, incorrect_guesses=card.incorrect_guesses)
    session.add(db_card)
    session.commit()
    session.refresh(db_card)
    return db_card

@app.get("/play", response_class = HTMLResponse)
async def getRandomCard(request:Request):
    return templates.TemplateResponse(request = request, name = "play.html", context = {"card": cardList[randint(0, len(cardList) - 1)]})

@app.get("/sets", response_class = HTMLResponse)
async def getSets(session: SessionDep, request:Request):
    sets = session.exec(select(Set).order_by(Set.name)).all()
    return templates.TemplateResponse(request=request, name="/sets.html", context={"sets":sets})
    # return templates.TemplateResponse(request = request, name = "sets.html", context = {"sets": setList})

@app.get("/users", response_class = HTMLResponse)
async def getUsers(request:Request):
    return templates.TemplateResponse(request = request, name = "users.html", context = {"users": userList})