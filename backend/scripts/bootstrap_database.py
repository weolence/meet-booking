from __future__ import annotations

import app.db.base  # noqa: F401
from app.config.settings import get_settings
from app.db.seed import seed_database
from app.db.session import SessionLocal, engine
from app.models.base import Base


def main() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as session:
        seed_database(session=session, settings=get_settings())
        session.commit()


if __name__ == "__main__":
    main()
