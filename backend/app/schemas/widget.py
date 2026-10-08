from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class LatestSubmissionInfo(BaseModel):
    id: int
    problem_id: int
    status: str
    language: str
    created_at: datetime


class WidgetSummary(BaseModel):
    total_submissions: int
    today_submissions: int
    total_accepted: int
    acceptance_rate: float
    solved_problems: int
    total_problems: int
    latest_submission: Optional[LatestSubmissionInfo] = None