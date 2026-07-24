# Repositories

Repositories wrap database queries and keep them out of services and routers.

- `BookingRepository` covers booking writes and taken-slot queries for a room/date pair.
- `RevokedTokenRepository` covers revoked token operations using token's hash
- `RoomRepository` manages rooms and their `RoomSlot` links.
- `SlotTemplateRepository` manages the reusable fixed time ranges.
- `UserRepository` manages users.
