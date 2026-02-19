from contextlib import asynccontextmanager

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import settings
from app.core.logger import logger
from app.utils.cache import CacheClient
from app.utils.http_client import HttpClient


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application startup...")

    HttpClient.get_client()
    CacheClient.init()

    yield

    logger.info("Application shutdown...")

    await HttpClient.close()
    await CacheClient.close()

    # await Tortoise.close_connections()
    # logger.info("Tortoise-ORM connections closed")


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(api_router, prefix=settings.API_PREFIX)

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=settings.DEBUG)
