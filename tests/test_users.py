import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.main import app, get_db
from app.models import Base

# Test database setup
TEST_DB_URL = "sqlite:///:memory:"
engine = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)


@pytest.fixture(scope="function")
def client():
    # Create tables in test database
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as c:
        yield c
    
    # Clean up
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


def test_create_user(client):
    r = client.post("/api/users",
                    json={"name": "Paul", "email": "pl@atu.ie", "age": 25, "student_id": "S1234567"})
    assert r.status_code == 201


def test_put_user(client):
    # Create a user first
    r = client.post("/api/users",
                    json={"name": "John", "email": "john@atu.ie", "age": 20, "student_id": "S1111111"})
    assert r.status_code == 201
    user_id = r.json()["id"]
    
    # Full update with PUT
    r = client.put(f"/api/users/{user_id}",
                   json={"name": "John Updated", "email": "johnupdated@atu.ie", "age": 21, "student_id": "S2222222"})
    assert r.status_code == 200
    assert r.json()["name"] == "John Updated"
    assert r.json()["age"] == 21


def test_patch_user(client):
    # Create a user first
    r = client.post("/api/users",
                    json={"name": "Jane", "email": "jane@atu.ie", "age": 22, "student_id": "S3333333"})
    assert r.status_code == 201
    user_id = r.json()["id"]
    
    # Partial update with PATCH
    r = client.patch(f"/api/users/{user_id}",
                     json={"age": 23})
    assert r.status_code == 200
    assert r.json()["age"] == 23
    assert r.json()["name"] == "Jane"  # Name should remain unchanged


def test_put_project(client):
    # Create a user first
    r = client.post("/api/users",
                    json={"name": "Bob", "email": "bob@atu.ie", "age": 25, "student_id": "S4444444"})
    user_id = r.json()["id"]
    
    # Create a project
    r = client.post("/api/projects",
                    json={"name": "Project A", "description": "Description A", "owner_id": user_id})
    assert r.status_code == 201
    project_id = r.json()["id"]
    
    # Full update with PUT
    r = client.put(f"/api/projects/{project_id}",
                   json={"name": "Project A Updated", "description": "New Description", "owner_id": user_id})
    assert r.status_code == 200
    assert r.json()["name"] == "Project A Updated"
    assert r.json()["description"] == "New Description"


def test_patch_project(client):
    # Create a user first
    r = client.post("/api/users",
                    json={"name": "Alice", "email": "alice@atu.ie", "age": 24, "student_id": "S5555555"})
    user_id = r.json()["id"]
    
    # Create a project
    r = client.post("/api/projects",
                    json={"name": "Project B", "description": "Description B", "owner_id": user_id})
    assert r.status_code == 201
    project_id = r.json()["id"]
    
    # Partial update with PATCH
    r = client.patch(f"/api/projects/{project_id}",
                     json={"description": "Updated Description"})
    assert r.status_code == 200
    assert r.json()["description"] == "Updated Description"
    assert r.json()["name"] == "Project B"  # Name should remain unchanged