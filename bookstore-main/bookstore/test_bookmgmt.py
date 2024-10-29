import sys
import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from unittest.mock import MagicMock
from bookstore.bookmgmt import router
from bookstore.database import Base, get_db, Book
from bookstore.middleware import JWTBearer

# Ensure the bookstore module is in the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

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

# Override the JWTBearer dependency
def override_jwt_bearer():
    return True

router.dependency_overrides[get_db] = override_get_db
router.dependency_overrides[JWTBearer] = override_jwt_bearer

client = TestClient(router)

@pytest.fixture(scope="module")
def setup_database():
    # Create the database schema
    Base.metadata.create_all(bind=engine)
    yield
    # Drop the database schema
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def mock_db():
    return MagicMock(spec=Session)

def test_create_book(mock_db, setup_database):
    book_data = {"name": "Test Book", "author": "Author", "published_year": 2021, "book_summary": "Summary"}
    mock_db.add.return_value = None
    mock_db.commit.return_value = None
    mock_db.refresh.return_value = None

    response = client.post("/books/", json=book_data)

    assert response.status_code == 200
    assert response.json()["name"] == "Test Book"

def test_update_book(mock_db, setup_database):
    book_data = {"name": "Updated Book", "author": "Author", "published_year": 2021, "book_summary": "Summary"}
    mock_db.query(Book).filter().first.return_value = Book(id=1, **book_data)

    response = client.put("/books/1", json=book_data)

    assert response.status_code == 200
    assert response.json()["name"] == "Updated Book"

def test_delete_book(mock_db, setup_database):
    mock_db.query(Book).filter().first.return_value = Book(id=1, name="Test Book", author="Author", published_year=2021, book_summary="Summary")

    response = client.delete("/books/1")

    assert response.status_code == 200
    assert response.json()["message"] == "Book deleted successfully"

def test_get_book_by_id(mock_db, setup_database):
    book_data = {"id": 1, "name": "Test Book", "author": "Author", "published_year": 2021, "book_summary": "Summary"}
    mock_db.query(Book).filter().first.return_value = Book(**book_data)

    response = client.get("/books/1")

    assert response.status_code == 200
    assert response.json()["name"] == "Test Book"

def test_get_all_books(mock_db, setup_database):
    book_data = [{"id": 1, "name": "Test Book", "author": "Author", "published_year": 2021, "book_summary": "Summary"}]
    mock_db.query(Book).all.return_value = [Book(**book_data[0])]

    response = client.get("/books/")

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["name"] == "Test Book"