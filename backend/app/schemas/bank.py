from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class BankCreate(BaseModel):
    name: str
    description: Optional[str] = None
    sort_order: int = 0


class BankUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    sort_order: Optional[int] = None


class BankResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: Optional[str]
    sort_order: int
    created_at: datetime


class BankWithCount(BaseModel):
    id: int
    name: str
    description: Optional[str]
    sort_order: int
    created_at: datetime
    problem_count: int