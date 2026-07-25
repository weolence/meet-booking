# ORM Models

The ORM layer is similar to database layer.

## Models

- `Role`
- `User`
- `Room`
- `SlotTemplate`
- `RoomSlot`
- `Booking`
- `RevokedToken`

`RoomSlot` is the key join model. It tells the system which slots belong to which rooms. `Booking` points to `room_slot_id`, not to room and slot separately.

## Shared pieces

- `base.py` — declarative base and naming convention
- `mixins.py` — shared integer `id`
- `db/base.py` — imports all models into one metadata tree

## Repositories

- `BookingRepository`
- `RevokedTokenRepository`
- `RoomRepository`
- `SlotTemplateRepository`
- `UserRepository`
