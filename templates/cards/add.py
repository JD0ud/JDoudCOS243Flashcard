from fastapi import APIRouter, Depends, Request, Form, HTTPException
from sqlmodel import select
from ...db.session import get_session, SessionDep
from ...db.models import Card, Set, User
from ...core.templates import templates
from fastapi.responses import HTMLResponse, RedirectResponse

router = APIRouter(prefix="/card")

@router.post("/add")
async def create_card(session: SessionDep, question: str = Form(...), answer: str = Form(...), set_id: int = Form(...)):
    db_card = Card(question=question, answer=answer, set_id=set_id)    
    session.add(db_card)
    session.commit()
    session.refresh(db_card)
    return RedirectResponse(url=f"/cards/{db_card.id}", status_code=302)