# App

This package contains the FastAPI application for the meeting-room booking
service. It wires HTTP requests to service-layer use cases and keeps database
details behind repositories.

Main package areas:

- `api/` defines routers, request/response schemas, and FastAPI dependencies.
- `config/` loads runtime settings from environment variables.
- `db/` owns the engine, session factory, and database bootstrap helpers.
- `models/` contains SQLAlchemy ORM models.
- `repositories/` contains database query and write helpers.
- `security/` contains password hashing and JWT helpers.
- `services/` contains business use cases and permission checks.

The dependency flow is:

`api -> services -> repositories -> db/models`
