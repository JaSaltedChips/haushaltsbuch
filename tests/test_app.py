"""HTTP smoke tests with isolated storage for fresh dependency installations."""

from fastapi.testclient import TestClient
import pytest

import database as db
import main
import reports


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_DIR", tmp_path)
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")
    with TestClient(main.app) as browser:
        yield browser
        browser.get("/logout", follow_redirects=False)


def test_login_static_assets_and_auth_gate(client):
    assert client.get("/login").status_code == 200
    assert client.get("/static/css/style.css").status_code == 200
    assert client.get("/api/accounts").status_code == 401
    assert client.get("/", follow_redirects=False).status_code == 303


def test_pin_setup_and_authenticated_pages_render(client):
    response = client.post("/login", data={"pin": "test-pin"}, follow_redirects=False)
    assert response.status_code == 303
    for path in ("/", "/setup", "/entry", "/transactions", "/report", "/export"):
        response = client.get(path)
        assert response.status_code == 200, path
        assert "text/html" in response.headers["content-type"]


def test_login_validation_templates_render(client):
    assert client.post("/login", data={"pin": "123"}).status_code == 400
    client.post("/login", data={"pin": "test-pin"})
    client.get("/logout")
    assert client.post("/login", data={"pin": "wrong-pin"}).status_code == 401


def test_chart_rendering_without_desktop():
    image = reports.chart_expense_by_category({"Groceries": 1234})
    assert image.startswith(b"\x89PNG\r\n\x1a\n")