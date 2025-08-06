from fastapi import APIRouter
from .actes import router as actes_router
from .suggestions import router as suggestions_router
from .validation import router as validation_router
from .audit import router as audit_router
from .admin import router as admin_router
from .auth import router as auth_router

api_router = APIRouter()

api_router.include_router(auth_router, prefix="/auth", tags=["authentication"])
api_router.include_router(actes_router, prefix="/actes", tags=["actes"])
api_router.include_router(suggestions_router, prefix="/suggestions", tags=["suggestions"])
api_router.include_router(validation_router, prefix="/validation", tags=["validation"])
api_router.include_router(audit_router, prefix="/audit", tags=["audit"])
api_router.include_router(admin_router, prefix="/admin", tags=["administration"])