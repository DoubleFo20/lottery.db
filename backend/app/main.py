from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app import database
from app.constants import HEALTH_PATH, HISTORY_PATH, STATUS_OK
from app.core.config import get_settings
from app.core.logging import setup_logging
from app.exceptions import register_exception_handlers
from app.repositories.lottery_draw import lottery_draw
from app.schemas.lottery_draw import LotteryHistoryItem, LotteryHistoryPage
from app.schemas.response import ApiResponse, ok_response
from app.services.history_seed_service import seed_history

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    database.init()
    with database.connect() as db:
        seed_history(db, Path(settings.history_csv_path))
    yield


app = FastAPI(title=settings.app_name, version=settings.app_version, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)


@app.get(HEALTH_PATH)
def health() -> dict[str, str]:
    database.verify()
    return {"status": STATUS_OK}


@app.get(HISTORY_PATH, response_model=ApiResponse[LotteryHistoryPage])
def history(
    db: Annotated[Session, Depends(database.get_db)],
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> ApiResponse[LotteryHistoryPage]:
    draws = lottery_draw.get_history_page(db, offset=offset, limit=limit)
    page = LotteryHistoryPage(
        items=[LotteryHistoryItem.model_validate(draw) for draw in draws],
        total=lottery_draw.count(db),
        offset=offset,
        limit=limit,
    )
    return ok_response(page)
