from fastapi.testclient import TestClient

from main import Calculator, app

client = TestClient(app)


def test_sums_2_numbers():
    assert Calculator().suma(2, 2) == 4


def test_resta_2_numbers():
    assert Calculator().resta(5, 3) == 2


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "miniproyecto-python"}
