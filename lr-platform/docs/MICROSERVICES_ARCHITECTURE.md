# LR Platform Microservices Architecture

The backend can now run as independent FastAPI services behind an API gateway.
The older monolith entrypoint is still present at `backend/api/main.py` for
local compatibility, but production traffic should enter through the gateway.

## Services

| Service | Public Port | Internal Port | Responsibility |
| --- | ---: | ---: | --- |
| `api-gateway` | `8000` | `8000` | Public HTTP entrypoint, CORS, path-based routing |
| `auth-service` | none | `8001` | Login and token creation under `/auth` |
| `user-service` | none | `8002` | User and role APIs under `/users` and `/roles` |
| `license-service` | none | `8003` | Product keys, trials, activation, and license status under `/license` |

## Request Flow

```text
Admin panel / frontend / agent
        |
        v
API Gateway :8000
        |
        +-- /auth/* -----> auth-service :8001 (internal)
        +-- /users/* ----> user-service :8002 (internal)
        +-- /roles/* ----> user-service :8002 (internal)
        +-- /license/* --> license-service :8003 (internal)
```

## Run Locally

1. Copy `.env.example` to `.env`.
2. Update secrets in `.env`.
3. Start the stack:

```bash
docker compose up --build
```

4. Open the gateway health endpoint:

```bash
curl http://localhost:8000/health
```

## Database

The services share MongoDB. Collections are created lazily by the application,
and startup seeders create default role documents when needed.

## Next Hardening Steps

- Give each service its own MongoDB database or collection namespace when domain ownership is stable.
- Move shared auth/database utilities into a versioned internal package.
- Add service-to-service authentication at the gateway boundary.
- Add independent CI jobs and image tags for each service.
- Add distributed tracing and structured request logs across the gateway and services.
