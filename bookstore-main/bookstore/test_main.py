import pytest
import httpx
from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from bookstore.database import Base, get_db
from bookstore.main import app
from bookstore.utils import create_access_token
from bookstore.database import UserCredentials, Book

# Create a test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Override the get_db dependency to use the test database
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="module")
def setup_database():
    # Create the database schema
    Base.metadata.create_all(bind=engine)
    yield
    # Drop the database schema
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client():
    with httpx.Client(app=app, base_url="http://test") as client:
        yield client

def test_signup(client, setup_database):
    response = client.post("/signup", json={"email": "test@example.com", "password": "testpassword"})
    assert response.status_code == 200
    assert response.json()["message"] == "User created successfully"

def test_login(client, setup_database):
    client.post("/signup", json={"email": "test@example.com", "password": "testpassword"})
    response = client.post("/login", json={"email": "test@example.com", "password": "testpassword"})
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_create_book(client, setup_database):
    client.post("/signup", json={"email": "test@example.com", "password": "testpassword"})
    login_response = client.post("/login", json={"email": "test@example.com", "password": "testpassword"})
    access_token = login_response.json()["access_token"]

    headers = {"Authorization": f"Bearer {access_token}"}
    book_data = {"name": "Test Book", "author": "Author", "published_year": 2021, "book_summary": "Summary"}
    response = client.post("/books/", json=book_data, headers=headers)
    assert response.status_code == 200
    assert response.json()["name"] == "Test Book"

def test_update_book(client, setup_database):
    client.post("/signup", json={"email": "test@example.com", "password": "testpassword"})
    login_response = client.post("/login", json={"email": "test@example.com", "password": "testpassword"})
    access_token = login_response.json()["access_token"]

    headers = {"Authorization": f"Bearer {access_token}"}
    book_data = {"name": "Test Book", "author": "Author", "published_year": 2021, "book_summary": "Summary"}
    create_response = client.post("/books/", json=book_data, headers=headers)
    book_id = create_response.json()["id"]

    updated_book_data = {"name": "Updated Book", "author": "Author", "published_year": 2021, "book_summary": "Updated Summary"}
    response = client.put(f"/books/{book_id}", json=updated_book_data, headers=headers)
    assert response.status_code == 200
    assert response.json()["name"] == "Updated Book"

def test_delete_book(client, setup_database):
    client.post("/signup", json={"email": "test@example.com", "password": "testpassword"})
    login_response = client.post("/login", json={"email": "test@example.com", "password": "testpassword"})
    access_token = login_response.json()["access_token"]

    headers = {"Authorization": f"Bearer {access_token}"}
    book_data = {"name": "Test Book", "author": "Author", "published_year": 2021, "book_summary": "Summary"}
    create_response = client.post("/books/", json=book_data, headers=headers)
    book_id = create_response.json()["id"]

    response = client.delete(f"/books/{book_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["message"] == "Book deleted successfully"

def test_get_book_by_id(client, setup_database):
    client.post("/signup", json={"email": "test@example.com", "password": "testpassword"})
    login_response = client.post("/login", json={"email": "test@example.com", "password": "testpassword"})
    access_token = login_response.json()["access_token"]

    headers = {"Authorization": f"Bearer {access_token}"}
    book_data = {"name": "Test Book", "author": "Author", "published_year": 2021, "book_summary": "Summary"}
    create_response = client.post("/books/", json=book_data, headers=headers)
    book_id = create_response.json()["id"]

    response = client.get(f"/books/{book_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["name"] == "Test Book"

def test_get_all_books(client, setup_database):
    client.post("/signup", json={"email": "test@example.com", "password": "testpassword"})
    login_response = client.post("/login", json={"email": "test@example.com", "password": "testpassword"})
    access_token = login_response.json()["access_token"]

    headers = {"Authorization": f"Bearer {access_token}"}
    book_data = {"name": "Test Book", "author": "Author", "published_year": 2021, "book_summary": "Summary"}
    client.post("/books/", json=book_data, headers=headers)

    response = client.get("/books/", headers=headers)
    assert response.status_code == 200
    assert len(response.json()) > 0
    assert response.json()[0]["name"] == "Test Book"