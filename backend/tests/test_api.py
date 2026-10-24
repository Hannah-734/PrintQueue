import os
os.environ["DATABASE_URL"] = "sqlite:///./test.db"

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, engine


@pytest.fixture()
def client():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    return TestClient(app)


def make(client, name="Bracket", material="PETG", deadline="2026-11-01"):
    r = client.post("/api/jobs", json={"name": name, "material": material, "deadline": deadline})
    assert r.status_code == 201
    return r.json()


def test_jobs_sorted_by_deadline_and_filtered(client):
    make(client, "Late", "PLA", "2026-12-01")
    make(client, "Soon", "PETG", "2026-11-01")
    assert [j["name"] for j in client.get("/api/jobs").json()] == ["Soon", "Late"]
    assert [j["name"] for j in client.get("/api/jobs?material=PLA").json()] == ["Late"]


def test_update_and_delete(client):
    job = make(client)
    r = client.patch(f"/api/jobs/{job['id']}", json={"status": "printing", "infill": 40})
    assert r.json()["status"] == "printing" and r.json()["infill"] == 40
    assert client.delete(f"/api/jobs/{job['id']}").status_code == 204
    assert client.get(f"/api/jobs/{job['id']}").status_code == 404


def test_inspection_pass_ships(client):
    job = make(client)
    client.patch(f"/api/jobs/{job['id']}", json={"status": "inspection"})
    r = client.post(f"/api/jobs/{job['id']}/inspection", json={"passed": True})
    assert r.json()["status"] == "shipped"


def test_inspection_fail_requeues_with_note(client):
    job = make(client)
    client.patch(f"/api/jobs/{job['id']}", json={"status": "inspection"})
    assert client.post(f"/api/jobs/{job['id']}/inspection", json={"passed": False}).status_code == 422
    r = client.post(f"/api/jobs/{job['id']}/inspection", json={"passed": False, "note": "Warped"})
    assert r.json()["status"] == "queued" and r.json()["inspection_note"] == "Warped"


def test_inspection_requires_inspection_stage(client):
    job = make(client)
    assert client.post(f"/api/jobs/{job['id']}/inspection", json={"passed": True}).status_code == 409


def test_printer_maintenance(client):
    p = client.post("/api/printers", json={"name": "Prusa MK4"}).json()
    r = client.post(f"/api/printers/{p['id']}/maintenance", json={"note": "Replaced nozzle"})
    assert r.json()["logs"][0]["note"] == "Replaced nozzle"
    assert client.post("/api/printers", json={"name": "Prusa MK4"}).status_code == 409
