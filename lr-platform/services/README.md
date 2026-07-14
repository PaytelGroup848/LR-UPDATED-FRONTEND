# Services

This folder contains the deployable microservices for LR Platform.

- `api-gateway`: public entrypoint that proxies requests to internal services.
- `auth-service`: authentication API.
- `user-service`: user and role management API.
- `license-service`: license, trial, activation, and hold APIs.

Each service owns its FastAPI application entrypoint and is wired in
`../docker-compose.yml`.
