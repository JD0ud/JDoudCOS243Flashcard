from fastapi import FastAPI
from pydantic import BaseModel
# from fastapi.templating import Jinja2Templates
from .core.templates import templates
from fastapi import Request, Form, WebSocket, WebSocketDisconnect, Cookie
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from .db.session import create_db_and_tables, SessionDep, get_session
from .db.models import Card, Set, User
from sqlmodel import Session, Field, SQLModel, create_engine, select, Relationship, update
from random import randint
from .routers import cards, sets

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load the DB
    create_db_and_tables()
    yield

app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(cards.router)
app.include_router(sets.router)

# templates = Jinja2Templates(directory = "templates")

# class Set(SQLModel, table = True):
#     id: int | None = Field(default = None, primary_key = True)
#     name: str
#     cards: list["Card"] = Relationship(back_populates = "set")
    # user_id: int

# class Card(SQLModel, table = True):
#     id:int | None = Field(default = None, primary_key = True)
#     question:str
#     answer:str
#     set_id: int | None = Field(default = None, foreign_key = "set.id")
#     set: Set | None = Relationship(back_populates = "cards")
#     incorrect_guesses: int

# class User(BaseModel):
#     id: int
#     name: str
#     email: str
#     set_id: int

class Deck(BaseModel):
    id: int
    name: int

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket:WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket:WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message:str):
        for connection in self.active_connections:
            await connection.send_text(message)
        
manager = ConnectionManager()

# setList = [
#     Set(id=1, name="Geography"),
#     Set(id=2, name="Animals"),
#     Set(id=3, name="Linguistics")
# ]

# cardList = [Card(id = 1, question = "Where is Taylor University located?", answer = "Upland, IN, USA", set_id = 1, incorrect_guesses = 0),
#             Card(id = 2, question = "What is the airspeed velocity of an unladen swallow?", answer = "~24 mph (European)", set_id = 2, incorrect_guesses = 0),
#             Card(id = 3, question = "What is a group of cats called?", answer = "Clowder", set_id = 2, incorrect_guesses = 0),
#             Card(id = 4, question = "What is the longest commonly accepted word in the English language?", answer = "Pneumonoultramicroscopicsilicovolcanoconiosis", set_id = 3, incorrect_guesses = 0),
#             Card(id = 5, question = "In which U.S. state is it illegal to eat fried chicken with a fork?", answer = "Georgia", set_id = 1, incorrect_guesses = 0)]

userList = [User(id = 1, name = "Monty123", email = "caerbannog@gmail.com", set_id = 2),
            User(id = 2, name = "helpicantthinkofaname", email = "helpicantthinkofanemail@yahoo.com", set_id = 1)]

@app.get("/", response_class = HTMLResponse)
async def root(session: SessionDep, request:Request):
    # return templates.TemplateResponse(request = request, name = "index.html", context = {"cards": cardList})
    cards = session.exec(select(Card).order_by(Card.id)).all()
    sets = session.exec(select(Set).order_by(Set.id)).all()
    return templates.TemplateResponse(request=request, name="/index.html", context={"cards":cards,"sets":sets})

@app.get("/cards")
async def getCards(q:str=""):
    searchResults = []
    for card in cardList:
        if q in card.question: searchResults.append(card)
    return searchResults

@app.get("/cards/{card_id}", response_class = HTMLResponse)
async def getCardByID(card_id:int, request:Request, session:SessionDep):
    # for card in cardList:
        # if card.id == card_id: return templates.TemplateResponse(request = request, name = "card.html", context = {"card": cardList[card_id - 1]})
    card = session.exec(select(Card).where(Card.id == card_id))
    return templates.TemplateResponse(request = request, name = "card.html", context = {"card":card})

@app.get("/sets/{set_id}", response_class = HTMLResponse)
async def getSetByID(session: SessionDep, set_id:int, request:Request):
    # for set in setList:
    #     if set.id == set_id: return templates.TemplateResponse(request = request, name = "set.html", context = {"set": cardList[card_id - 1]})
    # return None
    set = session.exec(select(Set).where(Set.id == set_id)).first()
    cards = set.cards
    return templates.TemplateResponse(request=request, name="/set.html", context={"set":set, "cards":cards})

@app.get("/set/add")
async def getAddSet(request:Request, session:SessionDep, response_class = HTMLResponse):
    return templates.TemplateResponse(request=request, name="/sets/add.html")

@app.post("/sets/add")
async def addSet(session: SessionDep, name:str = Form(...)):
    db_set = Set(name=name)
    session.add(db_set)
    session.commit()
    session.refresh(db_set)
    return db_set

@app.get("/card/add")
async def getAddCard(request:Request, session:SessionDep, response_class = HTMLResponse):
    sets = session.exec(select(Set)).all()
    return templates.TemplateResponse(request=request, name="/cards/add.html", context={"sets": sets})

@app.post("/card/add")
async def addCard(session: SessionDep, question: str = Form(...), answer: str = Form(...), set_id: int = Form(...)):
    db_card = Card(question=question, answer=answer, set_id=set_id, incorrect_guesses=0)    
    session.add(db_card)
    session.commit()
    session.refresh(db_card)
    return RedirectResponse(url=f"/cards/{db_card.id}", status_code=302)

@app.get("/cards/{card_id}/edit")
async def edit_card(request: Request, session:SessionDep, card_id:int):
    card = session.exec(select(Card).where(Card.id==card_id)).first()
    sets = session.exec(select(Set)).all()
    return templates.TemplateResponse(request=request, name="/cards/edit.html", context={"card":card, "sets":sets})

@app.post("/cards/{card_id}/edit")
async def edit_card(session:SessionDep, card_id:int, request:Request, response_class=HTMLResponse, question:str = Form(...), answer:str = Form(...), set_id:int = Form(...)):
    card = session.exec(select(Card).where(Card.id==card_id)).first()
    card.question = question
    card.answer = answer
    card.set_id = set_id
    session.commit()
    set = session.exec(select(Set).where(Set.id==set_id)).first()
    return templates.TemplateResponse(request=request, name="/set.html", context={"set":set})

@app.get("/{set_id}/edit")
async def edit_set(request: Request, session:SessionDep, set_id:int):
    set = session.exec(select(Set).where(Set.id==set_id)).first()
    sets = session.exec(select(Set)).all()
    return templates.TemplateResponse(request=request, name="/sets/add.html", context={"set":set, "sets":sets})

@app.post("/cards/{card_id}/delete")
async def deleteCard(request:Request, session:SessionDep, card_id:int):
    card = session.exec(select(Card).where(Card.id == card_id)).first()
    set_id = card.set_id
    session.delete(card)
    session.commit()
    return RedirectResponse(url=f"/sets/{set_id}", status_code=303)

@app.get("/{set_id}/delete")
async def deleteSet(request:Request, session:SessionDep, set_id:int):
    set = session.query(Set).filter(Set.id == set_id).first()
    session.delete(set)
    session.commit()

@app.get("/play", response_class = HTMLResponse)
async def getRandomCard(request:Request):
    return templates.TemplateResponse(request = request, name = "play.html", context = {"card": cardList[randint(0, len(cardList) - 1)]})

@app.get("/playWithFriends", response_class=HTMLResponse)
async def getPlayWithFriends(request:Request, session:SessionDep, response_class = HTMLResponse):
    return templates.TemplateResponse(request = request, name = "playWithFriends.html")

@app.post("/playWithFriends", response_class=HTMLResponse)
async def login(request:Request, session:SessionDep, response_class = HTMLResponse, username:str = Form(...)):
    response = templates.TemplateResponse(request = request, name = "playWithFriends.html", context = {"username": username})
    response.set_cookie(key="username", value=username, httponly=False)
    return response

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket:WebSocket, client_id:str, session:SessionDep):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            await manager.broadcast(f"{client_id} says: {data['payload']['message']}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(f"Client #{client_id} left the chat")

@app.get("/sets", response_class = HTMLResponse)
async def getSets(session: SessionDep, request:Request):
    sets = session.exec(select(Set).order_by(Set.name)).all()
    return templates.TemplateResponse(request=request, name="/sets/sets.html", context={"sets":sets})

@app.get("/users", response_class = HTMLResponse)
async def getUsers(request:Request):
    return templates.TemplateResponse(request = request, name = "/users/users.html", context = {"users": userList})