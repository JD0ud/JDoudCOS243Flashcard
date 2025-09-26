from fastapi import APIRouter, Depends, Request, Form, HTTPException
from sqlmodel import select
from ..db.session import get_session, SessionDep
from ..db.models import Card, Set, User
# from ..main import templates
from ..core.templates import templates
from fastapi.responses import HTMLResponse, RedirectResponse

#This prefix tell this router to handle everything going to "/cards/*"
router = APIRouter(prefix="/sets")

@router.get("/")
async def getSetByID(request:Request, session: SessionDep, set_id: int):
    sets = session.exec(select(Set).order_by(Set.id)).all()
    return templates.TemplateResponse(request=request, name="/sets/sets.html", context={"sets":sets})