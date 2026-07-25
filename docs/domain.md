# Domain

## Entities

### Role

Role lookup table. For now it only needs `user` and `admin`.

### User

Application user with a login, password hash, and a role.

### Room

A bookable room identified by its room number.

### SlotTemplate

A fixed time range such as `09:00-10:00`.

### RoomSlot

A valid room-slot pair.

### Booking

A reservation of one room slot on one date.

## Rules

- one room slot can have only one active booking per date
- users can cancel their own bookings
- admins can cancel any active booking
- fixed slots are part of the model, so arbitrary time ranges are out of scope

An active booking is a booking with `cancelled_by_user_login IS NULL`.
