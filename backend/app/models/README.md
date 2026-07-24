# Models

The ORM layer:

- `Role`
- `User`
- `Room`
- `SlotTemplate`
- `RoomSlot`
- `Booking`

`Revoked Token` is a base for holding revoked token's hash, using it logging out can be implemented later.

`Role` picked out from `User` because this decision makes easier migration to base with broader set of roles.
`SlotTemplate` is a base of slots, it allows removal of time duplicates in `RoomSlot` or `Booking`
`RoomSlot` is the source of truth for which slots a room supports. `Booking` points to `room_slot_id`, so the same room-slot pair is not stored twice.

An active booking is a row with `cancelled_by_user_login IS NULL`.

Lookup/resource tables use compact integer identifiers. `User` uses `login` as its primary
key. `Booking` uses the composite primary key `user_login`, `room_slot_id`, and
`booking_date`.
