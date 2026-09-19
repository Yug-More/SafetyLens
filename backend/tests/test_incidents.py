def test_list_incidents(client):
    response = client.get("/api/incidents")
    assert response.status_code == 200
    payload = response.json()
    assert payload["meta"]["count"] == 4
    assert payload["data"][0]["incident_code"] == "INC-2026-0042"


def test_severity_filter(client):
    response = client.get("/api/incidents?severity=high")
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 1
    assert data[0]["severity"] == "high"


def test_status_filter(client):
    response = client.get("/api/incidents?status=resolved")
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 2
    assert all(item["status"] == "resolved" for item in data)


def test_incident_details(client):
    response = client.get("/api/incidents/INC-2026-0042")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["incident"]["title"] == "Possible Worker Fall"
    assert data["camera"]["name"] == "Camera 04"
    assert len(data["evidence"]) == 2
    assert len(data["actions"]) == 5
    assert data["matched_procedure"]["procedure_code"] == "SOP-FALL-4.2"


def test_missing_incident_404(client):
    response = client.get("/api/incidents/INC-DOES-NOT-EXIST")
    assert response.status_code == 404
    payload = response.json()
    assert payload["error"]["code"] == "NOT_FOUND"


def test_invalid_severity(client):
    response = client.get("/api/incidents?severity=urgent")
    assert response.status_code == 422
    payload = response.json()
    assert payload["error"]["code"] == "VALIDATION_ERROR"
