from __future__ import annotations

from fastapi import APIRouter

from app.api.routers import auth_router, bookings_router, rooms_router, users_router


router = APIRouter()
router.include_router(auth_router)
router.include_router(users_router)
router.include_router(rooms_router)
router.include_router(bookings_router)
