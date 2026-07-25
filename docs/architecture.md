# Architecture

This service should stay a modular monolith.

The domain is small, the state changes are tightly connected, and the most
important consistency rule lives in the database: one room slot can have only
one active booking for a given date. Splitting this into several services would
add coordination problems without buying us much.

## Main flow

The booking path is straightforward on purpose:

`api -> services -> repositories -> db/models`

- `api` handles HTTP concerns, request parsing, auth dependencies, and response
  shaping.
- `services` should contain the actual use cases: book a slot, list
  availability, cancel a booking.
- `repositories` talk to the database and keep SQLAlchemy details out of the
  service layer.
- `db/` and `models/` hold persistence setup and table mappings.

`config/` and `security/` support the app from the side. They are not a domain
layer and they should not turn into a dumping ground.

## Booking flow

For `POST /bookings`, the expected sequence is:

1. The API receives the request and resolves the current user.
2. A service checks that the requested `room_slot` exists and that the action
   makes sense from a business point of view.
3. The repository attempts the insert.
4. The database remains the final guard against duplicate active bookings.

The app can check for conflicts first so it can return a cleaner error, but the
partial unique index is still the rule that actually protects the data.

Availability should be composed in the service layer:

1. Load the valid room slots for the requested room from `RoomRepository`.
2. Load the taken room slots for the requested room and date from
   `BookingRepository`.
3. Compute the difference to get the free slots.
