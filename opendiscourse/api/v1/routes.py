"""API route definitions for version 1 of the OpenDiscourse API."""

from fastapi import APIRouter
from api.routes.diagnostics import router as diagnostics_router

api_router = APIRouter()
api_router.include_router(diagnostics_router)
