# Operations Runbook

## Service Management
- **API Gateway (FastAPI)**: `python -m uvicorn services.api-gateway.main:app --host 0.0.0.0 --port 8000`
- **Web Frontend**: `python -m http.server 8080`
- **Health Checks**: `GET /health/live` & `GET /health/ready`
