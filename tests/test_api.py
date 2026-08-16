from fastapi.testclient import TestClient

from vehicle_maintenance.api import app


def test_local_api_domain_parity(monkeypatch, tmp_path):
    monkeypatch.setenv("VEHICLE_MAINT_DATA_DIR", str(tmp_path / "private"))
    client = TestClient(app)
    assert client.get("/api/status").status_code == 200
    code = client.get("/api/codes/A67")
    assert code.status_code == 200
    assert [rule["code"] for rule in code.json()] == ["A", "6", "7"]
    invalid = client.get("/api/codes/nope")
    assert invalid.status_code == 400
    result = client.post(
        "/api/decision/break-even",
        json={"dealer_cents": 32801, "alternative_cents": 16000},
    )
    assert result.json()["savings_cents"] == 16801
