# from fastapi import APIRouter, Depends, Request, Form, HTTPException
# from sqlmodel import select
# from ..db.session import get_session, SessionDep
# from ..db.models import Card, Set, User
# from ..main import templates, userList
# from fastapi.responses import HTMLResponse, RedirectResponse

# #This prefix tell this router to handle everything going to "/cards/*"
# router = APIRouter(prefix="/users")

# @router.get("/")
# async def getUsers(request:Request):
#     return templates.TemplateResponse(request = request, name = "users/users.html", context = {"users": userList})