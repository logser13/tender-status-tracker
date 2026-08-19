import os
import tempfile

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
from app.status import TenderStatus


def _build_test_session():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    url = f"sqlite:///{path}"
    engine = create_engine(url, connect_args={"check_same_thread": False})
    session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    return engine, session_local, path


def test_create_tender(client):
    response = client.post(
        "/tenders",
        json={"title": "Тендер A", "description": "Первый", "customer": "Заказчик 1"},
    )
    assert response.status_code == 201
    payload = response.json()
    assert payload["id"] > 0
    assert payload["status"] == TenderStatus.DRAFT.value


def test_get_tender(client):
    create = client.post(
        "/tenders", json={"title": "Тендер для получения", "description": "Описание"}
    )
    tender_id = create.json()["id"]

    response = client.get(f"/tenders/{tender_id}")
    assert response.status_code == 200
    assert response.json()["title"] == "Тендер для получения"


def test_get_missing_tender_returns_404(client):
    response = client.get("/tenders/999999")
    assert response.status_code == 404


def test_list_tenders_with_status_filter(client):
    client.post("/tenders", json={"title": "Черновик"})
    active_tender = client.post("/tenders", json={"title": "Будет активен"})
    active_id = active_tender.json()["id"]
    client.patch(
        f"/tenders/{active_id}/status",
        json={"new_status": "ACTIVE", "changed_by": "tester", "reason": "Активация"},
    )

    response = client.get("/tenders?status=ACTIVE")
    assert response.status_code == 200
    items = response.json()
    assert len(items) == 1
    assert items[0]["status"] == "ACTIVE"


def test_valid_status_update(client):
    create = client.post("/tenders", json={"title": "Проверка перехода"})
    tender_id = create.json()["id"]

    response = client.patch(
        f"/tenders/{tender_id}/status",
        json={"new_status": "ACTIVE", "changed_by": "operator", "reason": "Публикация"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "ACTIVE"


def test_invalid_status_transition_returns_409(client):
    create = client.post("/tenders", json={"title": "Неверный переход"})
    tender_id = create.json()["id"]

    response = client.patch(
        f"/tenders/{tender_id}/status",
        json={"new_status": "WON", "changed_by": "operator", "reason": "Баг"},
    )
    assert response.status_code == 409
    assert "Недопустимый переход статуса" in response.json()["detail"]

def test_status_history_records_change(client):
    create = client.post(
        "/tenders",
        json={"title": "История", "description": "Для истории"},
    )
    tender_id = create.json()["id"]
    client.patch(
        f"/tenders/{tender_id}/status",
        json={
            "new_status": "ACTIVE",
            "changed_by": "auditor",
            "reason": "Тестовый апрув",
        },
    )

    response = client.get(f"/tenders/{tender_id}/history")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["old_status"] == "DRAFT"
    assert data[0]["new_status"] == "ACTIVE"
    assert data[0]["changed_by"] == "auditor"
    assert data[0]["reason"] == "Тестовый апрув"


def test_edit_tender_fields(client):
    create = client.post("/tenders", json={"title": "Исходное"})
    tender_id = create.json()["id"]

    response = client.patch(
        f"/tenders/{tender_id}",
        json={"title": "Новое название", "customer": "ПАО Ромашка"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["title"] == "Новое название"
    assert payload["customer"] == "ПАО Ромашка"


@pytest.fixture(scope="function")
def client():
    engine, session_local, path = _build_test_session()

    def override_get_db():
        db = session_local()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.pop(get_db, None)
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    os.unlink(path)
