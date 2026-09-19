def test_list_procedures(client):
    response = client.get("/api/procedures")
    assert response.status_code == 200
    payload = response.json()
    assert payload["meta"]["count"] == 4
    titles = {item["title"] for item in payload["data"]}
    assert "Worker Fall Response" in titles


def test_worker_fall_procedure(client):
    response = client.get("/api/procedures/SOP-FALL-4.2")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["title"] == "Worker Fall Response"
    assert data["version"] == "4.2"
    assert len(data["steps"]) == 6
    assert "Notify the floor supervisor immediately." in data["steps"][0]
