# pytest

import pytest
from fastapi.testclient import TestClient
from fastapi.views import app 

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"} 

def test_articles():
    response = client.get("/articles")
    assert response.status_code == 200
    assert isinstance(response.json(), list) 

def test_create_article():
    article_data = {
        "title": "Test Article",
        "abstract": "This is a test abstract",
        "authors": [1, 2],
        "date": "2025-02-16"
    }
    response = client.post("/articles", json=article_data)
    assert response.status_code == 201
    assert response.json()["title"] == "Test Article"

def test_authors():
    response = client.get("/authors")
    assert response.status_code == 200
    assert isinstance(response.json(), list)  

def test_affiliations():
    response = client.get("/affiliations")
    assert response.status_code == 200
    assert isinstance(response.json(), list)  
