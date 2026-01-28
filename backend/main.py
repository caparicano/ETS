
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from backend.infrastructure.database import engine, Base
from backend.interfaces.api import documents, compliance, tasks, wizard, advisory, verifier
from backend.domain.exceptions import DomainError, RegulatoryComplianceError, TenantAccessError

# Create Tables (for MVP - usually done via Alembic)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="CeramETS Compliance API",
    description="EU ETS Compliance Platform for Ceramic Industry - Powered by AI",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# --- Global Exception Handlers (Hardening Phase 1) ---

@app.exception_handler(RegulatoryComplianceError)
async def regulatory_exception_handler(request: Request, exc: RegulatoryComplianceError):
    return JSONResponse(
        status_code=422,
        content={"detail": str(exc), "code": exc.code},
    )

@app.exception_handler(TenantAccessError)
async def tenant_exception_handler(request: Request, exc: TenantAccessError):
    return JSONResponse(
        status_code=403,
        content={"detail": str(exc), "code": exc.code},
    )

@app.exception_handler(DomainError)
async def domain_exception_handler(request: Request, exc: DomainError):
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc), "code": exc.code},
    )

# Include Routers
app.include_router(documents.router)
app.include_router(compliance.router)
app.include_router(tasks.router)
app.include_router(wizard.router)
app.include_router(advisory.router)
app.include_router(verifier.router)

@app.get("/")
def read_root():
    return {"message": "CeramETS Backend Operational"}
