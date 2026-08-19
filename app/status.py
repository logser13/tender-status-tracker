from enum import Enum


class TenderStatus(str, Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    WON = "WON"
    LOST = "LOST"


STATUS_LABELS = {
    TenderStatus.DRAFT: "Черновик",
    TenderStatus.ACTIVE: "Активен",
    TenderStatus.WON: "Выигран",
    TenderStatus.LOST: "Проигран",
}


ALLOWED_TRANSITIONS = {
    TenderStatus.DRAFT: {TenderStatus.ACTIVE},
    TenderStatus.ACTIVE: {TenderStatus.WON, TenderStatus.LOST},
    TenderStatus.WON: set(),
    TenderStatus.LOST: set(),
}


def is_transition_allowed(old_status: TenderStatus, new_status: TenderStatus) -> bool:
    return new_status in ALLOWED_TRANSITIONS.get(old_status, set())
