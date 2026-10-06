from fastapi import APIRouter

from app.api.v1.admin import router as admin_router
from app.api.v1.analytics import router as analytics_router
from app.api.v1.assessments import router as assessments_router
from app.api.v1.auth import router as auth_router
from app.api.v1.courses import router as courses_router
from app.api.v1.mastery import router as mastery_router
from app.api.v1.recommendations import router as recommendations_router
from app.api.v1.study_plans import router as study_plans_router
from app.api.v1.tutor import router as tutor_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(courses_router)
api_router.include_router(assessments_router)
api_router.include_router(mastery_router)
api_router.include_router(recommendations_router)
api_router.include_router(tutor_router)
api_router.include_router(study_plans_router)
api_router.include_router(analytics_router)
api_router.include_router(admin_router)
