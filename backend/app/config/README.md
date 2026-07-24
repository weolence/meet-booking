# Config

This package is for reading environment variables and turning them into a
single `Settings` object that the rest of the app can use.

All environment variables from `settings/config` should be initialized or values red by default should be changed before usage.

Seed settings:

- `DEFAULT_USER_ROLE_NAME`: role assigned during registration, defaults to `user`
- `SEED_ADMIN_LOGIN`: initial admin login, defaults to `admin`
- `SEED_ADMIN_PASSWORD`: initial admin password, defaults to `admin`

Readable environment variables (config):

- `APP_NAME`: name of application, used as FastAPI title
- `DATABASE_URL`: database address for engine initialization with specific dialect and port of database containeer
- `DB_ECHO`: defines existance of logs from database engine
- `DB_POOL_SIZE`: number of database connections kept open in the engine pool
- `DB_MAX_OVERFLOW`: number of extra database connections allowed above the pool size
- `JWT_SECRET_KEY`: secret key used for signing and verifying JWT access tokens
- `JWT_ALGORITHM`: algorithm used for JWT access token signing
- `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`: lifetime of JWT access tokens in minutes
