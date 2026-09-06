import pytest

import app as app_module
import storage


@pytest.fixture
def client(tmp_path, monkeypatch):
    # Point storage at a throwaway DB file for each test so tests don't
    # pollute each other or the real data/incidents.db.
    db_path = tmp_path / "test_incidents.db"
    monkeypatch.setattr(storage, "DATABASE_PATH", str(db_path))
    import config
    monkeypatch.setattr(config, "DATABASE_PATH", str(db_path))

    app_module.app.config["TESTING"] = True
    with app_module.app.test_client() as c:
        yield c


def test_ping(client):
    r = client.get("/api/ping")
    assert r.status_code == 200
    assert r.get_json() == {"status": "alive"}


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.get_json()
    assert body["status"] == "ok"
    assert "uptime_seconds" in body


def test_simulate_valid_scenario(client):
    r = client.post("/api/simulate", json={"scenario": "port_scan", "target": "127.0.0.1"})
    assert r.status_code == 200
    body = r.get_json()
    assert body["scenario"] == "port_scan"
    assert body["target"] == "127.0.0.1"
    assert "ai_summary" in body


def test_simulate_missing_body(client):
    r = client.post("/api/simulate", data="not json", content_type="application/json")
    assert r.status_code == 400
    assert "error" in r.get_json()


def test_simulate_missing_scenario(client):
    r = client.post("/api/simulate", json={"target": "127.0.0.1"})
    assert r.status_code == 400


def test_simulate_unknown_scenario(client):
    r = client.post("/api/simulate", json={"scenario": "totally_made_up"})
    assert r.status_code == 400
    assert "available_scenarios" in r.get_json()


def test_simulate_unsafe_target(client):
    r = client.post("/api/simulate", json={"scenario": "port_scan", "target": "8.8.8.8"})
    assert r.status_code == 400


def test_incidents_roundtrip(client):
    client.post("/api/simulate", json={"scenario": "malware_beacon"})
    r = client.get("/api/incidents")
    assert r.status_code == 200
    assert len(r.get_json()) == 1


def test_delete_incidents(client):
    client.post("/api/simulate", json={"scenario": "malware_beacon"})
    r = client.delete("/api/incidents")
    assert r.status_code == 200
    r = client.get("/api/incidents")
    assert r.get_json() == []


def test_metrics_empty(client):
    r = client.get("/api/metrics")
    assert r.status_code == 200
    assert r.get_json()["total_incidents"] == 0


def test_metrics_after_runs(client):
    client.post("/api/simulate", json={"scenario": "port_scan"})
    client.post("/api/simulate", json={"scenario": "syn_flood_lite"})
    r = client.get("/api/metrics")
    body = r.get_json()
    assert body["total_incidents"] == 2
    assert body["detection_rate"] == 100.0


def test_unknown_api_route_returns_json_404(client):
    r = client.get("/api/nonexistent")
    assert r.status_code == 404
    assert r.get_json() == {"error": "Not found"}


def test_index_page_renders(client):
    r = client.get("/")
    assert r.status_code == 200


def test_about_page_renders(client):
    r = client.get("/about")
    assert r.status_code == 200
