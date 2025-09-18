from fastapi import FastAPI
from fastapi.testclient import TestClient
import sys,os
from ..main import app

def test_read_main():
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert "Flashcard" in response.content.decode()
    print(sys.path)
    print(os.getcwd())
    assert 1==1