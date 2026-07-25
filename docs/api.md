# API

## Auth

### `POST /auth/register`

Registers a new user with the configured default role, `user` unless changed.

- `201 Created`
- `409 Conflict` if the login is already registered
- `422 Unprocessable Entity` if login or password is blank

### `POST /auth/login`

Accepts login and password. Returns a JWT access token.

- `200 OK`
- `401 Unauthorized`

## Users

### `GET /users/me`

Returns the current user.

## Availability

### `GET /availability?booking_date=YYYY-MM-DD`

Returns all rooms with their slots for the selected date. Each slot has
`is_available`.

## Bookings

### `GET /bookings/me`

Returns the current user's bookings.

Optional filters:

- `booking_date`

### `POST /bookings`

Creates a booking for the current user.

Body:

- `room_slot_id`
- `booking_date`

Responses:

- `201 Created`
- `404 Not Found` if the room slot does not exist
- `409 Conflict` if the slot is already booked for that date

### `DELETE /bookings/{room_slot_id}?booking_date=YYYY-MM-DD`

Cancels the active booking for a room slot and date.

- users can cancel their own bookings
- admins can cancel any active booking by room slot and date

Responses:

- `204 No Content`
- `403 Forbidden`
- `404 Not Found`

## Rooms and Slots

### `GET /rooms`

Lists rooms.

### `POST /rooms`

Creates a room. Admin only.

### `DELETE /rooms/{room_id}`

Removes a room. Admin only. Rooms with bookings are not removed.

### `GET /rooms/{room_id}/slots`

Lists slots assigned to one room.

### `PUT /rooms/{room_id}/slots`

Replaces slot templates assigned to one room. Admin only.

### `GET /rooms/{room_id}/availability?booking_date=YYYY-MM-DD`

Lists availability for one room and date.

### `GET /slot-templates`

Lists reusable fixed time ranges.
