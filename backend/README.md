# Backend

This is the service code for the meeting room app.

- `app/` is the runtime code.
- `migrations/` holds Alembic revisions.
- `tests/` is split into unit and integration coverage.
- `scripts/` is for local helpers that are useful during development but are not
  part of the app itself.

TODO:

- Finish the config and database wiring.
- Add Alembic migrations for the current models.
- Seed roles, rooms, slot templates, and room-slot links.
- Build auth on top of the new `security/` package.
