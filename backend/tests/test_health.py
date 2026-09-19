def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    payload = response.json()
    assert "data" in payload
    assert payload["data"]["status"] in {"ok", "degraded"}
    assert payload["data"]["app_name"]
    assert payload["data"]["database_status"] == "ok"
    assert "demo_mode" in payload["data"]
