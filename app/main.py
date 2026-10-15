"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .config import STATIC_DIR
from .database import init_db
from .routers.curriculums import router as curriculums_router
from .routers.pages import router as pages_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Prepare the local database when the application starts."""
    init_db()
    yield


app = FastAPI(title="Generador de CV · LAB21 del ISP21", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.include_router(pages_router)
app.include_router(curriculums_router)
