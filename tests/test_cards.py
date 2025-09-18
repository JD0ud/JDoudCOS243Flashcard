from fastapi.testclient import TestClient
from sqlmodel import Session, Field, SQLModel, create_engine, select, Relationship
import re
from ..main import app, get_session
from bs4 import BeautifulSoup

def test_read_cards():
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    # assert "Trivia" in response.content.decode()