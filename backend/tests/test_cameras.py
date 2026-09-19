def test_list_cameras(client):
    response = client.get("/api/cameras")
    assert response.status_code == 200
    payload = response.json()
    assert payload["meta"]["count"] == 12
    names = {item["name"] for item in payload["data"]}
    assert "Camera 04" in names
    assert "Camera 07" in names


def test_get_camera(client):
    response = client.get("/api/cameras/cam-04")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["name"] == "Camera 04"
    assert data["location"] == "Loading Zone B"
