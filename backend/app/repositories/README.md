# Repositories

Repositories wrap database queries and keep them out of services and routers.

- `booking_repository.py`
- `room_repository.py`
- `slot_template_repository.py`
- `user_repository.py`

- `BookingRepository` covers booking writes and taken-slot queries for a room/date pair.
- `RoomRepository` manages rooms and their `RoomSlot` links.
- `SlotTemplateRepository` manages the reusable fixed time ranges.
- `UserRepository` manages users.
