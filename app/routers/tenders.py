from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Tender, TenderStatusHistory
from app.schemas import (
    HistoryEntry,
    TenderCreate,
    TenderRead,
    TenderUpdate,
    StatusUpdateRequest,
)
from app.status import TenderStatus, is_transition_allowed

router = APIRouter(prefix="", tags=["tenders"])


@router.post(
    "/",
    response_model=TenderRead,
    status_code=status.HTTP_201_CREATED,
    summary="Создать тендер",
)
def create_tender(payload: TenderCreate, db: Session = Depends(get_db)) -> Tender:
    tender = Tender(
        title=payload.title,
        description=payload.description,
        customer=payload.customer,
        status=TenderStatus.DRAFT,
    )
    db.add(tender)
    db.commit()
    db.refresh(tender)
    return tender


@router.get(
    "/",
    response_model=list[TenderRead],
    summary="Получить список тендеров",
)
def list_tenders(
    status: TenderStatus | None = Query(default=None, description="Фильтр по статусу"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
) -> list[Tender]:
    query = db.query(Tender)
    if status is not None:
        query = query.filter(Tender.status == status)
    return query.order_by(Tender.id.asc()).offset(skip).limit(limit).all()


@router.get(
    "/{tender_id}",
    response_model=TenderRead,
    summary="Получить один тендер",
)
def get_tender(tender_id: int, db: Session = Depends(get_db)) -> Tender:
    tender = db.query(Tender).filter(Tender.id == tender_id).first()
    if not tender:
        raise HTTPException(status_code=404, detail="Тендер не найден.")
    return tender


@router.patch(
    "/{tender_id}",
    response_model=TenderRead,
    summary="Обновить данные тендера (без статуса)",
)
def update_tender(
    tender_id: int,
    payload: TenderUpdate,
    db: Session = Depends(get_db),
) -> Tender:
    tender = db.query(Tender).filter(Tender.id == tender_id).first()
    if not tender:
        raise HTTPException(status_code=404, detail="Тендер не найден.")

    payload_dict = payload.model_dump(exclude_unset=True)
    for field, value in payload_dict.items():
        setattr(tender, field, value)

    db.commit()
    db.refresh(tender)
    return tender


@router.patch(
    "/{tender_id}/status",
    response_model=TenderRead,
    summary="Обновить статус тендера с валидацией перехода",
)
def change_tender_status(
    tender_id: int,
    payload: StatusUpdateRequest,
    db: Session = Depends(get_db),
) -> Tender:
    tender = db.query(Tender).filter(Tender.id == tender_id).first()
    if not tender:
        raise HTTPException(status_code=404, detail="Тендер не найден.")

    new_status = payload.new_status
    old_status = tender.status

    if old_status == new_status:
        raise HTTPException(
            status_code=409,
            detail="Новый статус совпадает с текущим. Нет изменений.",
        )

    if not is_transition_allowed(old_status, new_status):
        raise HTTPException(
            status_code=409,
            detail=(
                f"Недопустимый переход статуса: {old_status.value} -> {new_status.value}."
            ),
        )

    history_entry = TenderStatusHistory(
        tender_id=tender.id,
        old_status=old_status,
        new_status=new_status,
        changed_by=payload.changed_by,
        reason=payload.reason,
        changed_at=datetime.now(timezone.utc),
    )

    tender.status = new_status
    db.add(history_entry)
    db.commit()
    db.refresh(tender)
    return tender


@router.get(
    "/{tender_id}/history",
    response_model=list[HistoryEntry],
    summary="Получить историю изменений статуса тендера",
)
def get_tender_status_history(
    tender_id: int,
    db: Session = Depends(get_db),
) -> list[TenderStatusHistory]:
    tender = db.query(Tender).filter(Tender.id == tender_id).first()
    if not tender:
        raise HTTPException(status_code=404, detail="Тендер не найден.")

    return (
        db.query(TenderStatusHistory)
        .filter(TenderStatusHistory.tender_id == tender_id)
        .order_by(desc(TenderStatusHistory.changed_at))
        .all()
    )
