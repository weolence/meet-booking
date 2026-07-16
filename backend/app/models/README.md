# Models

The ORM layer:

- `Role`
- `User`
- `Room`
- `SlotTemplate`
- `RoomSlot`
- `Booking`

`Role` picked out from `User` because this decision makes easier migration to base with broader set of roles.
`SlotTemplate` is a base of slots, it allows removal of time duplicates in `RoomSlot` or `Booking`
`RoomSlot` is the source of truth for which slots a room supports. `Booking` points to `room_slot_id`, so the same room-slot pair is not stored twice.

An active booking is a row with `cancelled_at IS NULL`.

`UUID` was chosen as unique id (PK) for tracking objects becuse even with possibility of composite primary key creation, it's easier to track objects with ids
