def test_system_status(client):
    response = client.get("/api/system/status")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["overall_status"] == "operational"
    assert data["demo_environment"] is True
    assert len(data["services"]) == 5


def test_demo_info(client):
    response = client.get("/api/demo/info")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["demo_mode"] is True
    assert data["facility"] == "Redwood Distribution Center"
    assert any("simulated" in item.lower() or "Stage 2" in item for item in data["limitations"])
