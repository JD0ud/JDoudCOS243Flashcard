from fastapi import APIRouter, Depends, Request, Form, HTTPException
from sqlmodel import select
from ..db.session import get_session, SessionDep
from ..db.models import Card, Set, User
from ..core.templates import templates
from fastapi.responses import HTMLResponse, RedirectResponse

#This prefix tell this router to handle everything going to "/cards/*"
router = APIRouter(prefix="/cards")

@router.get("/")
async def get_cards(request:Request, session:SessionDep):
    cards = session.exec(select(Card).order_by(Card.question)).all()
    return templates.TemplateResponse(request=request, name="/cards/cards.html", context={"cards":cards})

@router.get("/{card_id}/edit")
def edit_card(request: Request, session:SessionDep, card_id:int):
    card = session.exec(select(Card).where(Card.id==card_id)).first()
    sets = session.exec(select(Set)).all()
    return templates.TemplateResponse(request=request, name="/cards/add.html", context={"card":card, "sets":sets})