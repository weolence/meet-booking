# API

This package contains the HTTP layer for the booking service. It defines
FastAPI routers, request dependencies, response schemas, and service-error to
HTTP-error mapping.

Package includes:

- `routes.py` collects all routers into one root API router.
- `routers/` contains endpoint functions grouped by domain area.
- `schemas/` contains request and response models used by endpoints.
- `dependencies/` builds repositories, services, and current-user guards.
- `errors.py` converts service-layer exceptions into HTTP responses.

## Routers

`auth.py` handles authentication endpoints:

- register a new user with the default user role
- authenticate by login and password
- issue limited-lifetime JWT access tokens
- revoke the current access token on logout

Routes:

- `POST /auth/register` registers a new user.
- `POST /auth/login` accepts login and password and returns a JWT access token.
- `POST /auth/logout` revokes the current access token.

`users.py` handles user profile endpoints:

- return the current authenticated user

Routes:

- `GET /users/me` returns the current authenticated user.

`rooms.py` handles room, slot, and availability endpoints:

- list rooms
- let admins create and remove rooms
- list and update slot templates assigned to a room
- list availability for one room and date
- list availability for all rooms on one date
- list reusable slot templates

Routes:

- `GET /rooms` lists rooms.
- `POST /rooms` creates a room. Admin only.
- `DELETE /rooms/{room_id}` removes a room. Admin only.
- `GET /rooms/{room_id}/slots` lists slots assigned to one room.
- `PUT /rooms/{room_id}/slots` replaces slots assigned to one room. Admin only.
- `GET /rooms/{room_id}/availability?booking_date=YYYY-MM-DD` lists availability for one room and date.
- `GET /availability?booking_date=YYYY-MM-DD` lists availability for all rooms on one date.
- `GET /slot-templates` lists reusable fixed time slots.

`bookings.py` handles booking endpoints:

- list bookings owned by the current user
- create a booking for the current user
- cancel a booking through `DELETE /bookings/{room_slot_id}`
- allow admins to cancel another user's booking by passing `user_login`

Routes:

- `GET /bookings/me` lists bookings owned by the current user.
- `GET /bookings/me?booking_date=YYYY-MM-DD` lists the current user's bookings for one date.
- `POST /bookings` creates a booking for the current user.
- `DELETE /bookings/{room_slot_id}?booking_date=YYYY-MM-DD` cancels the current user's booking.
- `DELETE /bookings/{room_slot_id}?booking_date=YYYY-MM-DD&user_login={login}` lets an admin cancel another user's booking.
