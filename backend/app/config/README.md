# Config

This package is for reading environment variables and turning them into a
single `Settings` object that the rest of the app can use.

Defaults are enough for local Docker runs. For shared environments, change
database credentials, seed admin password, and JWT secret.

Seed settings:

- `DEFAULT_USER_ROLE_NAME`: role assigned during registration, defaults to `user`
- `SEED_ADMIN_LOGIN`: initial admin login, defaults to `admin`
- `SEED_ADMIN_PASSWORD`: initial admin password, defaults to `admin`

Runtime environment variables:

- `APP_NAME`: name of application, used as FastAPI title
- `DATABASE_URL`: SQLAlchemy database URL
- `DB_ECHO`: enables SQLAlchemy query logging
- `DB_POOL_SIZE`: number of database connections kept open in the engine pool
- `DB_MAX_OVERFLOW`: number of extra database connections allowed above the pool size
- `JWT_SECRET_KEY`: secret key used for signing and verifying JWT access tokens
- `JWT_ALGORITHM`: algorithm used for JWT access token signing
- `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`: lifetime of JWT access tokens in minutes
