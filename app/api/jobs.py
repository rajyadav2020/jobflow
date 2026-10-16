from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status as http_status

from app.schemas.jobs import JobCreate, JobCreated, JobList, JobRead, JobStatus
from app.services.job_store import InMemoryJobStore, get_job_store

router = APIRouter(prefix="/jobs", tags=["jobs"])

Store = Annotated[InMemoryJobStore, Depends(get_job_store)]


@router.post("", response_model=JobCreated, status_code=http_status.HTTP_201_CREATED)
def submit_job(payload: JobCreate, store: Store):
    job = store.create(payload)
    return JobCreated(id=job.id, status=job.status)


@router.get("", response_model=JobList)
def list_jobs(
    store: Store,
    status: JobStatus | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    items, total = store.list(status, limit, offset)
    return JobList(items=items, total=total, limit=limit, offset=offset)


@router.get("/{job_id}", response_model=JobRead)
def get_job(job_id: UUID, store: Store):
    job = store.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job