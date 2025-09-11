from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.templating import Jinja2Templates
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from random import randint

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory = "templates")

# groceryList = ["bread", "milk", "eggs", "ice cream", "more bread"]

class Card(BaseModel):
    id:int
    question:str
    answer:str
    set_id: int
    incorrect_guesses: int

class Set(BaseModel):
    id: int
    name: str
    user_id: int

class User(BaseModel):
    id: int
    name: str
    email: str
    set_id: int

class Deck(BaseModel):
    id: int
    name: int

setList = [
    Set(id=1, name="Geography", user_id=2),
    Set(id=2, name="Animals", user_id=1),
    Set(id=3, name="Linguistics", user_id=0)
]

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

@app.post("/card/add")
async def addCard(card:Card):
    cardList.append(card)
    return cardList

@app.get("/play", response_class = HTMLResponse)
async def getRandomCard(request:Request):
    return templates.TemplateResponse(request = request, name = "play.html", context = {"card": cardList[randint(0, len(cardList) - 1)]})

@app.get("/sets", response_class = HTMLResponse)
async def getSets(request:Request):
    return templates.TemplateResponse(request = request, name = "sets.html", context = {"sets": setList})

@app.get("/users", response_class = HTMLResponse)
async def getUsers(request:Request):
    return templates.TemplateResponse(request = request, name = "users.html", context = {"users": userList})