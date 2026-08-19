from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import Base, engine
from app.routers.tenders import router as tenders_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Tender Status Tracker",
    description=(
        "Сервис для управления статусами тендеров с историей изменений "
        "на уровне каждой операции обновления статуса."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(tenders_router, prefix="/tenders")
