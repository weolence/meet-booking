# Services

## AuthService

`AuthService` is responsible for authentication-related use cases:

- authenticate a user by login and password
- register a new user with the default user role
- create an access token for an authenticated user
- logout a user by revoking the current access token

It uses:

- `UserRepository` for user and role reads and writes
- `RevokedTokenRepository` to store revoked access tokens

## BookingService

`BookingService` is responsible for booking-related use cases:

- create a booking for an existing room slot and user
- return or reactivate an existing booking for the same user, room slot, and date
- reject duplicate active bookings for the same room slot and date
- cancel a booking
- enforce cancellation permissions:
  users can cancel their own bookings, admins can cancel any booking

It uses:

- `BookingRepository` for booking reads and writes
- `RoomRepository` to verify that the requested room slot exists
- `UserRepository` to verify that the acting user exists

## RoomService

`RoomService` is responsible for room and room-slot use cases:

- list all rooms
- create a room
- remove a room
- list all room slots for a room
- list room-slot availability for a room and date
- change which slot templates are available for a room

The room-slot update flow is implemented as synchronization:

- slot links missing from the requested set are created
- slot links not present in the requested set are removed
- removal is rejected when existing bookings still reference the room slot

It uses:

- `RoomRepository` for room and room-slot operations
- `BookingRepository` for taken-slot lookup
- `SlotTemplateRepository` to validate requested slot templates

## Errors

Services raise domain-oriented exceptions from `errors.py` instead of leaking
database details upward. The main groups are:

- `ValidationError` for invalid input or invalid state transitions
- `NotFoundError` for missing rooms, room slots, bookings, users, or slot templates
- `ConflictError` for duplicate rooms, duplicate bookings, or room-slot removal conflicts
- `PermissionDeniedError` for actions blocked by access rules
