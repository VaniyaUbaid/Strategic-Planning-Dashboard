from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.common.schemas import HealthResponse, SystemModulesStatusResponse
from backend.common.auth_router import router as auth_router
from backend.decision import decision_router
from backend.finance import finance_router
from backend.research import research_router
from backend.student import student_router

app = FastAPI(
    title="Institutional Decision Platform API",
    description="Unified enterprise intelligence backend supporting Student, Financial, Research, and Decision Assistant modules.",
    version="1.0.0",
)

# CORS Configuration for local frontend development
origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://localhost:5174",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Module Routers
app.include_router(auth_router)
app.include_router(student_router)
app.include_router(finance_router)
app.include_router(research_router)
app.include_router(decision_router)


@app.get("/api/health", tags=["System"], response_model=HealthResponse)
def health_check():
    """System health check endpoint."""
    return HealthResponse(status="ok")


@app.get("/api/modules/status", tags=["System"], response_model=SystemModulesStatusResponse)
def get_modules_status():
    """Return platform-wide operational readiness status for all intelligence modules."""
    return SystemModulesStatusResponse(
        student="ready",
        finance="ready",
        research="ready",
        decision_assistant="ready",
    )
