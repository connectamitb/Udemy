# Student guide

## Purpose

This public demo API returns stable fictional data so you can learn HTTP requests, JSON validation, and AI-agent integrations without credentials or real customer/payment information.

Use `/docs` to try requests, `/openapi.json` for OpenAPI 3 clients, and `postman_collection.json` for an importable collection.

## Beginner exercises

1. Retrieve customer 1 and identify its membership.
2. Retrieve order 102 and calculate its total from quantity × unit price.
3. Retrieve payment 103 and explain its simulated `declined` status.
4. Compare normal system health with `?scenario=high_memory`.
5. Use Python `requests.get(base_url + "/health")` and print the status and JSON.

Negative tests: request customer 999 (404), customer `abc` (422), and customer 1 with `scenario=server_error` (500). Try `scenario=missing_email` and validate the response against the normal customer schema. Unknown scenarios return 400.

## Power Automate: CheckCustomerAPI

Create a flow named `CheckCustomerAPI` with a Number input `ExpectedID`. Add an HTTP action: Method `GET`; URI `https://YOUR-RENDER-URL/api/v1/customers/1`; no authentication. Add a condition that the HTTP action status code equals `200`. On failure, return an explicit failure object containing the HTTP status and error body—do not parse a successful customer from a failed action. On success, parse JSON, compare `body('HTTP')?['id']` to `ExpectedID`, and return `HttpStatus`, `ActualID`, and `ValidationResult`. Return `PASS` only when both status is 200 and IDs match. Thus ExpectedID 1 is PASS and ExpectedID 2 is FAIL because the endpoint deliberately returns customer 1. Verify your tenant’s HTTP connector licensing and possible premium-connector requirements before teaching this flow.

## Copilot Studio exercise

Agent description: “A classroom assistant that queries the fictional DevTest Lab API and explains JSON validation results.” Instructions: “Use only the API tool for demo records, identify simulated scenarios clearly, never claim fictional data is real, and report HTTP failures explicitly.” Tool description: “GET a read-only DevTest Lab API endpoint; base URL is the instructor-provided HTTPS URL.” Ask: “What is customer 1?”, “Is system web-01 healthy?”, and “Show the high-memory training scenario.”

Troubleshooting: wake a sleeping Render free service, confirm the HTTPS URL (including no trailing path errors), inspect the status code in `/docs`, and remember that scenario responses are intentionally simulated failures.
