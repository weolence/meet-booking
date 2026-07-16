# App Structure

This package holds the application code for the booking service.

- `api/` is where the FastAPI routers, request dependencies, and response
  wiring live.
- `config/` holds runtime settings loaded from the environment.
- `security/` is reserved for password hashing, JWT helpers, and shared auth
  checks.
- `db/` is the database plumbing: engine, session factory, and metadata
  exports.
- `models/` contains the SQLAlchemy models that mirror the schema.
- `repositories/` wraps query logic and write operations.
- `schemas/` is for request and response models.
- `services/` is where booking and availability use cases should go.

The dependency flow is still simple:

`api -> services -> repositories -> db/models`

`config/` and `security/` support the flow, but they are not a separate business
layer.
