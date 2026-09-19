def test_dashboard_summary(client):
    response = client.get("/api/dashboard/summary")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["total_cameras"] == 12
    assert data["active_cameras"] == 12
    assert data["open_incidents"] >= 1
    assert data["average_response_time_seconds"] == 42
    assert data["facility_name"] == "Redwood Distribution Center"


def test_dashboard_activity(client):
    response = client.get("/api/dashboard/activity?limit=5")
    assert response.status_code == 200
    payload = response.json()
    assert len(payload["data"]) <= 5
    assert payload["meta"]["limit"] == 5
    assert payload["meta"]["count"] >= 5
