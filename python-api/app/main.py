from __future__ import annotations

from contextlib import asynccontextmanager
import os

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .database import create_db_and_tables
from .errors import APIError
from .routers.games import router as games_router
from .schemas import ErrorResponse


@asynccontextmanager
async def lifespan(_: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(title="Tic-Tac-Toe API", version="1.0.0", lifespan=lifespan)

cors_origins_raw = os.getenv("CORS_ORIGINS", "http://localhost:4000")
cors_origins = [origin.strip() for origin in cors_origins_raw.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(APIError)
async def handle_api_error(_, exc: APIError) -> JSONResponse:
    payload = ErrorResponse(error=exc.error, message=exc.message, valid_moves=exc.valid_moves)
    return JSONResponse(status_code=exc.status_code, content=payload.model_dump())


@app.exception_handler(RequestValidationError)
async def handle_validation_error(_, exc: RequestValidationError) -> JSONResponse:
    payload = ErrorResponse(
        error="invalid_payload",
        message="Invalid request payload. Provide integers x and y in the request body.",
    )
    return JSONResponse(status_code=422, content=payload.model_dump())


@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(games_router)
