def test_list_procedures(client):
    response = client.get("/api/procedures")
    assert response.status_code == 200
    payload = response.json()
    assert payload["meta"]["count"] == 4
    titles = {item["title"] for item in payload["data"]}
    assert "Worker Fall and Person-Down Response" in titles


def test_worker_fall_procedure(client):
    response = client.get("/api/procedures/SOP-FALL-4.2")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["title"] == "Worker Fall and Person-Down Response"
    assert data["version"] == "4.2"
    assert data["is_sample"] is True
    assert data["chunk_count"] >= 1
    joined = " ".join(data["steps"])
    assert "Notify the floor supervisor immediately" in joined
    assert "medical" in joined.lower()

    chunks = client.get("/api/procedures/SOP-FALL-4.2/chunks")
    assert chunks.status_code == 200
    chunk_payload = chunks.json()["data"]
    assert len(chunk_payload) >= 3
    assert all(item["content"].strip() for item in chunk_payload)
