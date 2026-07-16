# DB Layer

- `base.py` gathers the model metadata so Alembic and the app see one schema.
- `session.py` owns the engine and session factory. It reads connection settings
  from `app.config`.
