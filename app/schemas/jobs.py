from datetime import date, datetime
from enum import Enum
from typing import Annotated, Any, Literal, Union
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class JobStatus(str, Enum):
    queued = "queued"
    running = "running"
    completed = "completed"
    failed = "failed"


# ---------- Per-task inputs ----------
class ReportInput(BaseModel):
    report_type: Literal["sales", "inventory", "users"]
    date_from: date
    date_to: date
    format: Literal["pdf", "csv"] = "pdf"

    @model_validator(mode="after")
    def check_date_order(self):
        if self.date_to < self.date_from:
            raise ValueError("date_to must be on or after date_from")
        return self


class ImportInput(BaseModel):
    file_name: str = Field(min_length=1, pattern=r"^.+\.csv$")
    delimiter: Literal[",", ";", "\t"] = ","
    has_header: bool = True


class NotificationInput(BaseModel):
    channel: Literal["email", "sms"]
    recipient: str = Field(min_length=3)
    message: str = Field(min_length=1, max_length=500)


# ---------- Requests: one model per job type ----------
class ReportJobCreate(BaseModel):
    type: Literal["report"]
    input: ReportInput


class ImportJobCreate(BaseModel):
    type: Literal["import"]
    input: ImportInput


class NotificationJobCreate(BaseModel):
    type: Literal["notification"]
    input: NotificationInput


# `type` decides which model validates `input`
JobCreate = Annotated[
    Union[ReportJobCreate, ImportJobCreate, NotificationJobCreate],
    Field(discriminator="type"),
]


# ---------- Responses ----------
class JobCreated(BaseModel):
    id: UUID
    status: JobStatus


class JobRead(BaseModel):
    id: UUID
    type: str
    input: dict[str, Any]
    status: JobStatus
    result: dict[str, Any] | None = None
    error_message: str | None = None
    attempt_count: int = 0
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None


class JobList(BaseModel):
    items: list[JobRead]
    total: int
    limit: int
    offset: int