from fastapi import APIRouter

from app.api.v1 import admin, ads, auth, company, users


api_router = APIRouter()

# IMPORTANT: don't add extra prefixes here — routers already define them
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(ads.router)
api_router.include_router(admin.router)
api_router.include_router(company.router)
