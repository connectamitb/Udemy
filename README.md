# DevTest Lab API

DevTest Lab API is a small, read-only FastAPI application for practicing REST integrations with Copilot Studio, Power Automate, Postman, cURL, Python, and Playwright. Every customer, order, payment, and system metric is fictional and deterministic. It does not process payments or monitor infrastructure.

## Run locally

Requires Python 3.12+.

```bash
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Open http://localhost:8000, Swagger at http://localhost:8000/docs, and the OpenAPI 3 schema at http://localhost:8000/openapi.json. The separately authored Swagger 2.0 document for custom connector tooling is `openapi-v2.json`; it is intentionally not a renamed OpenAPI 3 document.

## Endpoints and scenarios

`GET /api/v1/customers/{id}`, `/orders/{id}`, `/payments/{id}`, and `/systems/{id}/health` return fictional records. `GET /health` reports application availability. Add `scenario=missing_email`, `server_error`, `not_found`, `high_memory`, `service_down`, or `slow_response` where supported. Unsupported scenarios return a structured 400. Scenario changes are request-scoped and never mutate fixtures. `slow_response` waits 150ms and is bounded below two seconds.

All errors use `{ "error": { "code": "...", "message": "..." } }`. A modest per-client in-process limit protects public demos; Render instances are ephemeral, so this is an abuse safeguard, not a distributed quota system.

## Tests

```bash
pytest
```

## GitHub and Render deployment

1. Create an empty GitHub repository and push this project: `git init`, `git add .`, `git commit -m "Initial DevTest Lab API"`, `git branch -M main`, `git remote add origin https://github.com/YOUR_NAME/YOUR_REPO.git`, then `git push -u origin main`.
2. Create a Render account and choose **New → Web Service**.
3. Connect the GitHub repository and select the free plan (or an always-on plan for dependable classroom/agent calls).
4. Use build command `pip install -r requirements.txt` and start command `uvicorn main:app --host 0.0.0.0 --port $PORT`. `render.yaml` supplies these settings when using Blueprint deployment.
5. Deploy, then open the HTTPS URL Render provides and append `/docs`. Do not assume a URL before Render creates the service.
6. Test from another computer with `curl https://YOUR-RENDER-URL/health` and import `postman_collection.json` after setting `baseUrl`.
7. Push changes to GitHub to trigger redeploys. The free service may sleep after inactivity, has usage limits, and has an ephemeral filesystem; this app therefore stores no user data. Choose an always-on paid plan if Copilot Studio/Power Automate requires consistent latency and availability.

No API keys or student registration are required. Configure `CORS_ORIGINS` only when browser clients need specific origins; leave it unset for the simple demo default.

## Integrations

See [STUDENT_GUIDE.md](STUDENT_GUIDE.md) for exercises and [INSTRUCTOR_GUIDE.md](INSTRUCTOR_GUIDE.md) for lecture and Power Automate material.
