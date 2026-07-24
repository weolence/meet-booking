from app.api.routers.auth import router as auth_router
from app.api.routers.bookings import router as bookings_router
from app.api.routers.rooms import router as rooms_router
from app.api.routers.users import router as users_router

__all__ = [
    "auth_router",
    "bookings_router",
    "rooms_router",
    "users_router",
]
