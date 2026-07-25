# Database

The schema has seven tables:

- `roles`
- `users`
- `rooms`
- `slot_templates`
- `room_slots`
- `bookings`
- `revoked_tokens`

Lookup/resource tables use integer ids. `users.login` is the user primary key.
`bookings` uses a composite primary key.

## Tables

### `roles`

- `id`
- `role`

Constraints:

- `CHECK length(btrim(role)) > 0`
- `UNIQUE (role)`

### `users`

- `login`
- `password_hash`
- `role_id`

Constraints and indexes:

- `CHECK length(btrim(login)) > 0`
- `CHECK length(btrim(password_hash)) > 0`
- `FOREIGN KEY role_id -> roles.id`

### `rooms`

- `id`
- `name`

Constraints:

- `CHECK length(btrim(name)) > 0`
- `UNIQUE (name)`

### `slot_templates`

- `id`
- `start_time`
- `end_time`

Constraints:

- `CHECK end_time > start_time`
- `UNIQUE (start_time, end_time)`

### `room_slots`

- `id`
- `room_id`
- `slot_template_id`

Constraints and indexes:

- `FOREIGN KEY room_id -> rooms.id`
- `FOREIGN KEY slot_template_id -> slot_templates.id`
- `UNIQUE (room_id, slot_template_id)`
- index on `slot_template_id`

This table defines which slots each room actually supports.

### `bookings`

- `user_login`
- `room_slot_id`
- `booking_date`
- `cancelled_by_user_login`

Constraints and indexes:

- `FOREIGN KEY room_slot_id -> room_slots.id`
- `FOREIGN KEY user_login -> users.login`
- `FOREIGN KEY cancelled_by_user_login -> users.login`
- primary key on `(user_login, room_slot_id, booking_date)`
- partial unique index on `(room_slot_id, booking_date)` where `cancelled_by_user_login IS NULL`
- index on `(user_login, booking_date)`
- partial index on `(booking_date, room_slot_id)` where `cancelled_by_user_login IS NULL`

An active booking is a row where `cancelled_by_user_login IS NULL`.

### `revoked_tokens`

- `id`
- `token_hash`
- `user_login`
- `expires_at`
- `revoked_at`

Constraints and indexes:

- `FOREIGN KEY user_login -> users.login`
- unique index on `token_hash`
- index on `expires_at`
- index on `user_login`

## Why bookings point to `room_slot`

`room_slots` already defines a valid room-slot pair. Storing `room_id` and `slot_template_id` again inside `bookings` would duplicate that pair for no gain. `room_slot_id` keeps the model tighter and makes the main uniqueness rule simpler.
