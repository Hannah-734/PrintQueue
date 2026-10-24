"""Run with: pytest  (pip install pytest httpx)"""
import os
os.environ["DATABASE_URL"] = "sqlite:///./test.db"

from fastapi.testclient import TestClient
from main import app


def test_job_lifecycle():
    with TestClient(app) as client:
        printers = client.get("/api/printers").json()
        assert len(printers) >= 1

        job = client.post("/api/jobs", json={
            "name": "Bracket v2", "material": "PETG",
            "deadline": "2030-01-15", "printer_id": printers[0]["id"],
            "infill_pct": 40,
        }).json()
        assert job["status"] == "queued"

        client.patch(f"/api/jobs/{job['id']}", json={"status": "inspection"})
        failed = client.post(f"/api/jobs/{job['id']}/inspections",
                             json={"result": "fail", "notes": "warped"}).json()
        assert failed["status"] == "queued"

        client.patch(f"/api/jobs/{job['id']}", json={"status": "inspection"})
        passed = client.post(f"/api/jobs/{job['id']}/inspections",
                             json={"result": "pass"}).json()
        assert passed["status"] == "shipped"
        assert len(passed["inspections"]) == 2

        assert client.patch(f"/api/jobs/{job['id']}", json={"status": "bogus"}).status_code == 422
        assert client.delete(f"/api/jobs/{job['id']}").status_code == 204
        assert client.get(f"/api/jobs/{job['id']}").status_code == 404


def test_maintenance():
    with TestClient(app) as client:
        p = client.get("/api/printers").json()[0]
        out = client.post(f"/api/printers/{p['id']}/maintenance",
                          json={"task": "Replaced nozzle"}).json()
        assert out["last_maintenance_at"] is not None
