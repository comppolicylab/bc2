import logging

from fastapi import FastAPI, Request

from .config import config
from .generated import app as generated_app

logger = logging.getLogger(__name__)


async def lifespan(_: FastAPI):
    """Create the database if it doesn't exist."""
    if not await config.db.driver.exists():
        logger.warning("No database exists, creating a new one")
        await config.db.driver.create()

    yield


app = FastAPI(lifespan=lifespan)


@app.middleware("http")
async def begin_db_session(request: Request, call_next):
    async with config.db.driver.async_session() as session:
        request.state.db = session
        try:
            response = await call_next(request)
            session.commit()
            return response
        except Exception as e:
            session.rollback()
            raise e


app.mount("/api/v1", generated_app)
