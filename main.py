from __future__ import annotations

import asyncio
import os
import time
from collections import defaultdict, deque
from copy import deepcopy
from typing import Annotated, Literal

from fastapi import FastAPI, Path, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, ConfigDict, Field
from starlette.exceptions import HTTPException as StarletteHTTPException


APP_NAME = "DevTest Lab API"
VERSION = "1.0.0"
Scenario = Literal["normal", "missing_email", "server_error", "not_found", "high_memory", "service_down", "slow_response"]


class ErrorBody(BaseModel):
    error: dict[str, str]


class Customer(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: int
    name: str
    email: str
    status: Literal["active", "inactive"]
    membership: Literal["standard", "silver", "gold"]


class CustomerWithoutEmail(BaseModel):
    id: int
    name: str
    status: Literal["active", "inactive"]
    membership: Literal["standard", "silver", "gold"]


class OrderItem(BaseModel):
    product: str
    quantity: Annotated[int, Field(gt=0)]
    unit_price: Annotated[float, Field(ge=0)]


class Order(BaseModel):
    order_id: int
    customer_id: int
    items: list[OrderItem]
    total: float
    currency: str
    status: Literal["confirmed", "processing", "shipped"]


class Payment(BaseModel):
    payment_id: int
    order_id: int
    amount: float
    currency: str
    status: Literal["completed", "pending", "declined"]
    transaction_reference: str


class SystemHealth(BaseModel):
    system_id: str
    cpu_percent: int
    memory_percent: int
    disk_percent: int
    service_status: Literal["running", "unavailable"]
    health: Literal["healthy", "degraded", "unavailable"]
    data_source: str = "simulated training data"


CUSTOMERS = {
    1: Customer(id=1, name="Sarah Johnson", email="sarah.johnson@example.com", status="active", membership="gold"),
    2: Customer(id=2, name="Michael Chen", email="michael.chen@example.com", status="active", membership="silver"),
    3: Customer(id=3, name="Aisha Williams", email="aisha.williams@example.com", status="active", membership="standard"),
    4: Customer(id=4, name="Daniel Garcia", email="daniel.garcia@example.com", status="inactive", membership="silver"),
    5: Customer(id=5, name="Priya Patel", email="priya.patel@example.com", status="active", membership="gold"),
}
ORDERS = {
    101: Order(order_id=101, customer_id=1, items=[OrderItem(product="Wireless Mouse", quantity=2, unit_price=25.0)], total=50.0, currency="USD", status="confirmed"),
    102: Order(order_id=102, customer_id=2, items=[OrderItem(product="USB-C Hub", quantity=1, unit_price=39.99), OrderItem(product="HDMI Cable", quantity=2, unit_price=12.50)], total=64.99, currency="USD", status="shipped"),
    103: Order(order_id=103, customer_id=3, items=[OrderItem(product="Mechanical Keyboard", quantity=1, unit_price=89.0)], total=89.0, currency="USD", status="processing"),
    104: Order(order_id=104, customer_id=4, items=[OrderItem(product="Webcam", quantity=1, unit_price=59.95)], total=59.95, currency="USD", status="confirmed"),
    105: Order(order_id=105, customer_id=5, items=[OrderItem(product="Laptop Stand", quantity=2, unit_price=44.50)], total=89.0, currency="USD", status="confirmed"),
}
PAYMENTS = {
    101: Payment(payment_id=101, order_id=101, amount=50.0, currency="USD", status="completed", transaction_reference="SIM-TXN-101"),
    102: Payment(payment_id=102, order_id=102, amount=64.99, currency="USD", status="pending", transaction_reference="SIM-TXN-102"),
    103: Payment(payment_id=103, order_id=103, amount=89.0, currency="USD", status="declined", transaction_reference="SIM-TXN-103"),
    104: Payment(payment_id=104, order_id=104, amount=59.95, currency="USD", status="completed", transaction_reference="SIM-TXN-104"),
    105: Payment(payment_id=105, order_id=105, amount=89.0, currency="USD", status="completed", transaction_reference="SIM-TXN-105"),
}
SYSTEMS = {
    "web-01": SystemHealth(system_id="web-01", cpu_percent=35, memory_percent=48, disk_percent=52, service_status="running", health="healthy"),
    "api-01": SystemHealth(system_id="api-01", cpu_percent=42, memory_percent=51, disk_percent=47, service_status="running", health="healthy"),
}
SUPPORTED = {
    "customer": {"normal", "missing_email", "server_error", "not_found", "slow_response"},
    "order": {"normal", "server_error", "not_found", "slow_response"},
    "payment": {"normal", "server_error", "not_found", "slow_response"},
    "system": {"normal", "high_memory", "service_down", "server_error", "not_found", "slow_response"},
}


def error(code: str, message: str, status: int) -> JSONResponse:
    return JSONResponse(status_code=status, content={"error": {"code": code, "message": message}})


async def apply_scenario(kind: str, scenario: str, resource: str) -> None:
    if scenario not in SUPPORTED[kind]:
        raise ScenarioError("UNSUPPORTED_SCENARIO", f"Scenario '{scenario}' is not supported for this endpoint.", 400)
    if scenario == "slow_response":
        await asyncio.sleep(0.15)
    if scenario == "server_error":
        raise ScenarioError("SIMULATED_SERVER_ERROR", "A controlled server error was requested for training.", 500)
    if scenario == "not_found":
        raise ScenarioError(f"{resource.upper()}_NOT_FOUND", f"The requested {resource} does not exist.", 404)


class ScenarioError(Exception):
    def __init__(self, code: str, message: str, status: int):
        self.code, self.message, self.status = code, message, status


app = FastAPI(title=APP_NAME, version=VERSION, description="A fictional, read-only REST API for API integration and validation training.", docs_url="/docs", redoc_url="/redoc")
app.add_middleware(CORSMiddleware, allow_origins=[x.strip() for x in os.getenv("CORS_ORIGINS", "*").split(",")], allow_methods=["GET"], allow_headers=["*"])

_requests: dict[str, deque[float]] = defaultdict(deque)
RATE_LIMIT, RATE_WINDOW = 120, 60


@app.middleware("http")
async def rate_limit(request: Request, call_next):
    if request.url.path == "/health":
        return await call_next(request)
    key = request.client.host if request.client else "unknown"
    now = time.monotonic()
    hits = _requests[key]
    while hits and now - hits[0] > RATE_WINDOW:
        hits.popleft()
    if len(hits) >= RATE_LIMIT:
        return error("RATE_LIMITED", "Too many requests. Please retry shortly.", 429)
    hits.append(now)
    return await call_next(request)


@app.exception_handler(ScenarioError)
async def scenario_exception(_: Request, exc: ScenarioError):
    return error(exc.code, exc.message, exc.status)


@app.exception_handler(StarletteHTTPException)
async def http_exception(_: Request, exc: StarletteHTTPException):
    return error("HTTP_ERROR", str(exc.detail), exc.status_code)


@app.exception_handler(RequestValidationError)
async def validation_exception(_: Request, __: RequestValidationError):
    return error("VALIDATION_ERROR", "The request contains an invalid value.", 422)


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def homepage():
    return HTMLResponse("""<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width'><title>DevTest Lab API</title><style>body{font:16px system-ui;line-height:1.6;max-width:900px;margin:auto;padding:2rem;color:#172033;background:#f5f7fb}header,section{background:white;border-radius:14px;padding:1.5rem;margin:1rem 0;box-shadow:0 4px 18px #14213d12}h1{color:#3454d1}a{color:#3454d1}code{background:#eef1ff;padding:.15rem .35rem;border-radius:4px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:1rem}</style></head><body><header><h1>DevTest Lab API</h1><p>A safe, fictional, read-only REST API for practicing Copilot Studio, Power Automate, Postman, Python requests, cURL, and Playwright.</p><p><a href='/docs'>Open interactive Swagger documentation →</a> · <a href='/openapi.json'>OpenAPI schema</a></p></header><div class='grid'><section><h2>Customers</h2><p><a href='/api/v1/customers/1'>GET /api/v1/customers/1</a></p></section><section><h2>Orders</h2><p><a href='/api/v1/orders/101'>GET /api/v1/orders/101</a></p></section><section><h2>Payments</h2><p><a href='/api/v1/payments/101'>GET /api/v1/payments/101</a></p></section><section><h2>System health</h2><p><a href='/api/v1/systems/web-01/health'>GET /api/v1/systems/web-01/health</a></p></section></div><section><h2>Using this API</h2><p>Import <code>postman_collection.json</code> into Postman, or paste an endpoint into a Power Automate HTTP action or Copilot Studio tool. Add scenarios such as <code>?scenario=missing_email</code> to practice validation. All records and metrics are fictional training data; no authentication or real payment processing is involved.</p></section></body></html>""")


@app.get("/health", tags=["Service"], summary="Check API availability")
async def health():
    return {"status": "healthy", "service": APP_NAME, "version": VERSION}


@app.get("/api/v1/customers/{customer_id}", response_model=Customer | CustomerWithoutEmail, responses={404: {"model": ErrorBody}, 422: {"model": ErrorBody}, 500: {"model": ErrorBody}}, tags=["Customers"])
async def get_customer(customer_id: Annotated[int, Path(gt=0, description="Positive fictional customer ID")], scenario: Annotated[str, Query(description="Controlled training scenario")] = "normal"):
    await apply_scenario("customer", scenario, "customer")
    customer = CUSTOMERS.get(customer_id)
    if not customer:
        raise ScenarioError("CUSTOMER_NOT_FOUND", f"Customer {customer_id} does not exist.", 404)
    result = deepcopy(customer.model_dump())
    if scenario == "missing_email":
        result.pop("email")
    return result


@app.get("/api/v1/orders/{order_id}", response_model=Order, responses={404: {"model": ErrorBody}, 500: {"model": ErrorBody}}, tags=["Orders"])
async def get_order(order_id: Annotated[int, Path(gt=0)], scenario: Annotated[str, Query()] = "normal"):
    await apply_scenario("order", scenario, "order")
    order = ORDERS.get(order_id)
    if not order:
        raise ScenarioError("ORDER_NOT_FOUND", f"Order {order_id} does not exist.", 404)
    return deepcopy(order)


@app.get("/api/v1/payments/{payment_id}", response_model=Payment, responses={404: {"model": ErrorBody}, 500: {"model": ErrorBody}}, tags=["Payments"])
async def get_payment(payment_id: Annotated[int, Path(gt=0)], scenario: Annotated[str, Query()] = "normal"):
    await apply_scenario("payment", scenario, "payment")
    payment = PAYMENTS.get(payment_id)
    if not payment:
        raise ScenarioError("PAYMENT_NOT_FOUND", f"Payment {payment_id} does not exist.", 404)
    return deepcopy(payment)


@app.get("/api/v1/systems/{system_id}/health", response_model=SystemHealth, responses={404: {"model": ErrorBody}, 500: {"model": ErrorBody}}, tags=["Systems"])
async def get_system_health(system_id: str, scenario: Annotated[str, Query()] = "normal"):
    await apply_scenario("system", scenario, "system")
    system = SYSTEMS.get(system_id)
    if not system:
        raise ScenarioError("SYSTEM_NOT_FOUND", f"System {system_id} does not exist.", 404)
    result = system.model_dump()
    if scenario == "high_memory":
        result.update(memory_percent=96, health="degraded")
    elif scenario == "service_down":
        result.update(service_status="unavailable", health="unavailable")
    return result


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", "8000")), reload=False)
