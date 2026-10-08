from fastapi.testclient import TestClient

from main import ORDERS, app

client = TestClient(app)


def test_customer_success_and_shape():
    response = client.get("/api/v1/customers/1")
    assert response.status_code == 200
    assert response.json()["email"] == "sarah.johnson@example.com"


def test_customer_not_found_and_invalid_id():
    assert client.get("/api/v1/customers/999").status_code == 404
    assert client.get("/api/v1/customers/nope").status_code == 422
    assert client.get("/api/v1/customers/0").status_code == 422


def test_order_total_and_relationship():
    body = client.get("/api/v1/orders/102").json()
    assert body["customer_id"] == 2
    assert round(sum(i["quantity"] * i["unit_price"] for i in body["items"]), 2) == body["total"]
    assert body["total"] == ORDERS[102].total


def test_payment_success():
    body = client.get("/api/v1/payments/101").json()
    assert body["order_id"] == 101 and body["status"] == "completed"


def test_scenarios():
    assert client.get("/api/v1/customers/1?scenario=missing_email").status_code == 200
    assert "email" not in client.get("/api/v1/customers/1?scenario=missing_email").json()
    assert client.get("/api/v1/customers/1?scenario=server_error").status_code == 500
    assert client.get("/api/v1/systems/web-01/health?scenario=high_memory").json()["memory_percent"] == 96
    assert client.get("/api/v1/systems/web-01/health?scenario=service_down").json()["service_status"] == "unavailable"
    assert client.get("/api/v1/customers/1?scenario=unknown").status_code == 400


def test_slow_response_is_bounded():
    import time
    start = time.monotonic()
    response = client.get("/api/v1/customers/1?scenario=slow_response")
    assert response.status_code == 200
    assert time.monotonic() - start < 2


def test_openapi_and_health():
    assert client.get("/health").json()["status"] == "healthy"
    schema = client.get("/openapi.json").json()
    assert schema["openapi"].startswith("3.")
    assert "/api/v1/customers/{customer_id}" in schema["paths"]


def test_error_shape():
    body = client.get("/api/v1/orders/999").json()
    assert set(body) == {"error"}
    assert {"code", "message"} == set(body["error"])
