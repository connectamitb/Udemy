# Instructor guide

## Architecture

`main.py` contains a FastAPI app, Pydantic response models, immutable fixture definitions, request-scoped scenario transformations, structured exception handling, conservative GET-only CORS, and a modest in-process rate limit. There is no database, authentication, credential storage, external service, or writable shared state. Render runs Uvicorn and uses `/health` as its health check.

## Lecture flow

Start at the landing page, open `/docs`, call customer 1, follow its related order and payment, then compare normal and `high_memory` system health. Demonstrate 404, 422, 500, and `missing_email` validation. Import the Postman collection and build `CheckCustomerAPI` in Power Automate. Expected results: normal customer 1 is 200, unknown customer is 404, invalid ID is 422, server error is 500, high memory is 200 with memory 96, and ExpectedID 2 fails the ID comparison.

## Operations and maintenance

Deploy via Render using the README instructions. Monitor `/health` from an external uptime check if desired; it only proves application availability, not real infrastructure health. Render free instances sleep and have ephemeral storage, so no data is expected to persist. For classroom reliability and lower cold-start risk, use an always-on plan. Keep dependencies updated, run `pytest`, and review the generated OpenAPI document after endpoint changes.

## Troubleshooting and extensions

Check Render logs for startup/import errors, verify `$PORT` is used, and test `/health` before student calls. A future course can add pagination, a repository-backed sample dataset, authentication exercises, webhooks, or a separate test service—but should keep real payment and personal data out of the public demo.
