from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class SubmissionCreate(BaseModel):
    problem_id: int
    code: str = Field(min_length=1, max_length=100_000)
    language: str = Field(default="python", max_length=20)


class SubmissionSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    problem_id: int
    language: str
    status: str
    passed_cases: int
    total_cases: int
    created_at: datetime


class SubmissionDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    problem_id: int
    code: str
    language: str
    status: str
    runtime_ms: Optional[int] = None
    memory_kb: Optional[int] = None
    passed_cases: int
    total_cases: int
    error_message: Optional[str] = None
    created_at: datetime


class SubmissionListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[SubmissionSummary]