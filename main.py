from fastapi import FastAPI
from pydantic import BaseModel
from core.templates import templates
from fastapi import Request, Form, WebSocket, WebSocketDisconnect, Cookie
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from db.session import create_db_and_tables, SessionDep, get_session
from db.models import Card, Set, User
from sqlmodel import Session, Field, SQLModel, create_engine, select, Relationship, update
from random import randint
# from routers import cards, sets
import random
from sqlalchemy.sql.expression import func

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load the DB
    create_db_and_tables()
    yield

app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")

# app.include_router(cards.router)
# app.include_router(sets.router)

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

    async def send_personal_message(self, message:str, websocket:WebSocket):
        await websocket.send_text(message)
        
manager = ConnectionManager()

userList = [User(id = 1, name = "Monty123", email = "caerbannog@gmail.com", set_id = 2),
            User(id = 2, name = "helpicantthinkofaname", email = "helpicantthinkofanemail@yahoo.com", set_id = 1)]

@app.get("/", response_class = HTMLResponse)
async def root(session: SessionDep, request:Request):
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
    card = session.exec(select(Card).where(Card.id == card_id)).first()
    return templates.TemplateResponse(request = request, name = "card.html", context = {"card":card})

@app.get("/sets/{set_id}", response_class = HTMLResponse)
async def getSetByID(session: SessionDep, set_id:int, request:Request):
    set = session.exec(select(Set).where(Set.id == set_id)).first()
    cards = set.cards
    return templates.TemplateResponse(request=request, name="/set.html", context={"set":set, "cards":cards})

@app.get("/set/add")
async def getAddSet(request:Request, session:SessionDep, response_class = HTMLResponse):
    return templates.TemplateResponse(request=request, name="/sets/add.html")

@app.post("/sets/add")
async def addSet(request:Request, session: SessionDep, response_class = HTMLResponse, name:str = Form(...)):
    db_set = Set(name=name)
    session.add(db_set)
    session.commit()
    session.refresh(db_set)
    sets = session.exec(select(Set).order_by(Set.name)).all()
    return templates.TemplateResponse(request=request, name="/sets/sets.html", context={"sets":sets})

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
    cards = session.exec(select(Card).order_by(Card.id))
    return templates.TemplateResponse(request = request, name = "playWithFriends.html", context = {"cards":cards})

@app.post("/playWithFriends", response_class=HTMLResponse)
async def login(request:Request, session:SessionDep, response_class = HTMLResponse, username:str = Form(...)):
    cards = session.exec(select(Card).order_by(Card.id))
    response = templates.TemplateResponse(request = request, name = "playWithFriends.html", context = {"username": username, "cards":cards})
    response.set_cookie(key="username", value=username, httponly=False)
    return response

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket:WebSocket, client_id:str, session:SessionDep):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            if 'message' in data['payload']:
                await manager.broadcast(f"{client_id} | {data['payload']['message']}")
            elif 'command' in data['payload']:
                if ".loadplayer" in data['payload']['command']:
                    if data['payload']['command'] == ".loadplayer":
                        await manager.broadcast(f".loadplayer {client_id}")
                    else:
                        await manager.broadcast(f".loadplayer {client_id} | {data['payload']['command'][12:]}")
                elif data['payload']['command'][:12] == '.getquestion':
                    try:
                        int(data['payload']['command'][13])
                        card = session.exec(select(Card).where(Card.id==int(data['payload']['command'][13:]))).first()
                    except ValueError:
                        setsPassed = data['payload']['command'][13:]
                        print(setsPassed.split(','))
                        sets = session.exec(select(Set).where(Set.name.in_(setsPassed.split(','))).order_by(Set.id)).all()
                        setIDs = []
                        for i in sets:
                            setIDs.append(i.id)
                        print(setIDs)
                        card = session.exec(select(Card).where(Card.set_id.in_(setIDs)).order_by(func.random())).first()
                    await manager.broadcast(f".getquestion {card.question}")
                    await manager.broadcast(f".getanswer {card.answer}")
                elif data['payload']['command'][:12] == ".firstanswer":
                    await manager.broadcast(f"{data['payload']['command']}")
                else: await manager.broadcast(f"{data['payload']['command']}")
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