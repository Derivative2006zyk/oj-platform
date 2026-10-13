from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, model_validator


def _infer_submission_kind(language: str) -> str:
    if language == "choice":
        return "choice"
    if language == "fill_blank":
        return "fill_blank"
    if language == "proof":
        return "proof"
    return "code"


class SubmissionCreate(BaseModel):
    problem_id: int
    language: str = "python"
    code: Optional[str] = None
    answer_data: Optional[dict[str, Any]] = None

    @model_validator(mode="after")
    def _check_payload(self):
        kind = _infer_submission_kind(self.language)
        if kind == "code":
            if not self.code:
                raise ValueError("code is required for code submissions")
        else:
            if self.answer_data is None:
                raise ValueError("answer_data is required for choice/fill_blank/proof submissions")
        return self


class SubmissionDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    problem_id: int
    submission_kind: str
    code: Optional[str]
    language: str
    answer_data: Optional[dict[str, Any]]
    status: str
    runtime_ms: Optional[int]
    memory_kb: Optional[int]
    passed_cases: int
    total_cases: int
    error_message: Optional[str]
    created_at: datetime


class SubmissionListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[SubmissionDetail]