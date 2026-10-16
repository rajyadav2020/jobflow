from datetime import datetime, timezone
from functools import lru_cache
from uuid import UUID, uuid4

from app.schemas.jobs import JobCreate, JobRead, JobStatus


class InMemoryJobStore:
    def __init__(self) -> None:
        self._jobs: dict[UUID, JobRead] = {}

    def create(self, payload: JobCreate) -> JobRead:
        job = JobRead(
            id=uuid4(),
            type=payload.type,
            input=payload.input.model_dump(mode="json"),
            status=JobStatus.queued,
            created_at=datetime.now(timezone.utc),
        )
        self._jobs[job.id] = job
        return job

    def get(self, job_id: UUID) -> JobRead | None:
        return self._jobs.get(job_id)

    def list(
        self, status: JobStatus | None, limit: int, offset: int
    ) -> tuple[list[JobRead], int]:
        jobs = sorted(self._jobs.values(), key=lambda j: j.created_at, reverse=True)
        if status:
            jobs = [j for j in jobs if j.status == status]
        return jobs[offset : offset + limit], len(jobs)


@lru_cache  # one shared instance for the whole process
def get_job_store() -> InMemoryJobStore:
    return InMemoryJobStore()