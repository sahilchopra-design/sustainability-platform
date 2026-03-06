import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import structlog

from database import init_db, settings
from api.v1.router import api_router

log = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("A2 Data Hub starting", port=settings.port)
    await init_db()
    log.info("Database initialised")
    yield
    log.info("A2 Data Hub shutting down")


app = FastAPI(
    title="A2 Intelligence — Reference Data Hub",
    description=(
        "Centralised reference data module. Ingests 103 public data sources, "
        "normalises to common schema, and serves structured data to all "
        "A2 Intelligence platform modules via versioned REST API."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://localhost:5174", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "A2 Data Hub",
        "version": "1.0.0",
        "port": settings.port,
    }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    log.error("Unhandled exception", path=request.url.path, error=str(exc))
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error": str(exc)},
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=settings.port, reload=False)
