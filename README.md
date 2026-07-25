# Meet Booking

FastAPI service for booking meeting rooms in a coworking.

Users can see room availability, create bookings, and cancel their own active
bookings. Admins can manage rooms and slots, and can cancel any active booking.

## Stack

- FastAPI
- PostgreSQL
- SQLAlchemy
- JWT-based auth

## Run with Docker

Build the app image:

```sh
docker build -t meet-booking .
```

Create a persistent database volume and network:

```sh
docker volume create meet-booking-postgres-data
docker network create meet-booking-net
```

If they already exist, skip those two commands.

Start PostgreSQL:

```sh
docker run -d --name meet-booking-postgres --network meet-booking-net \
  -e POSTGRES_DB=meet_booking \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -v meet-booking-postgres-data:/var/lib/postgresql/data \
  postgres:16-alpine
```

Start the app:

```sh
docker run --rm --name meet-booking --network meet-booking-net \
  -p 8000:8000 \
  -e DATABASE_URL=postgresql+psycopg://postgres:postgres@meet-booking-postgres:5432/meet_booking \
  -e SEED_ADMIN_LOGIN=admin \
  -e SEED_ADMIN_PASSWORD=admin \
  meet-booking
```

The API will be available at `http://localhost:8000`.

Data is stored in PostgreSQL. On startup the app creates missing tables and
inserts seed data if it is not there yet:

- admin user: `admin` / `admin`
- rooms: `101`, `102`, `103`
- fixed one-hour slots from `09:00` to `17:00`

The `meet-booking-postgres-data` volume keeps the database between container
restarts.

## Run with Docker Compose

```sh
docker compose up --build
```

Compose starts the app and PostgreSQL together. The database uses the
`postgres_data` volume and is bootstrapped the same way as the plain Docker run.

The API is exposed at `http://localhost:8001`.

## Run locally

Set `DATABASE_URL` to a PostgreSQL database and run:

```sh
poetry install
poetry run python backend/scripts/bootstrap_database.py
poetry run uvicorn app.main:app --app-dir backend --reload
```

## Examples

Login:

```sh
curl -s http://localhost:8000/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"login":"admin","password":"admin"}'
```

Save the returned token:

```sh
TOKEN=...
```

Check availability:

```sh
curl -s 'http://localhost:8000/availability?booking_date=2026-07-25' \
  -H "Authorization: Bearer $TOKEN"
```

Create a booking:

```sh
curl -s http://localhost:8000/bookings \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"room_slot_id":1,"booking_date":"2026-07-25"}'
```

Cancel the active booking for a room slot and date:

```sh
curl -i -X DELETE 'http://localhost:8000/bookings/1?booking_date=2026-07-25' \
  -H "Authorization: Bearer $TOKEN"
```

## Tests

```sh
poetry run pytest
```

## Useful endpoints

- `POST /auth/register`
- `POST /auth/login`
- `POST /auth/logout`
- `GET /users/me`
- `GET /rooms`
- `GET /rooms/{room_id}/slots`
- `GET /rooms/{room_id}/availability?booking_date=YYYY-MM-DD`
- `GET /availability?booking_date=YYYY-MM-DD`
- `GET /bookings/me`
- `POST /bookings`
- `DELETE /bookings/{room_slot_id}?booking_date=YYYY-MM-DD`
