from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List

class SubprojectCreate(BaseModel):
    title: str
    description: str
    hint: Optional[str] = None
    reference_links: List[dict] = []
    answer_guide: Optional[str] = None
    sort_order: int = 0

class TestCaseCreate(BaseModel):
    input_data: str
    expected_output: str
    is_example: bool = True

class ProblemCreate(BaseModel):
    title: str
    category_id: int
    description: str
    type: str
    difficulty: int = Field(ge=1, le=5)
    tags: List[str] = []
    answer: Optional[str] = None
    explanation: Optional[str] = None
    options: Optional[List[dict]] = None
    blanks: Optional[List[dict]] = None
    test_cases: List[TestCaseCreate] = []
    subprojects: List[SubprojectCreate] = []

class ProblemUpdate(BaseModel):
    title: Optional[str] = None
    category_id: Optional[int] = None
    description: Optional[str] = None
    type: Optional[str] = None
    difficulty: Optional[int] = Field(None, ge=1, le=5)
    tags: Optional[List[str]] = None
    answer: Optional[str] = None
    explanation: Optional[str] = None
    options: Optional[List[dict]] = None
    blanks: Optional[List[dict]] = None
    test_cases: Optional[List[TestCaseCreate]] = None
    subprojects: Optional[List[SubprojectCreate]] = None

class ProblemSummary(BaseModel):
    id: int
    title: str
    type: str
    difficulty: int
    tags: List[str]
    category_id: int
    model_config = ConfigDict(from_attributes=True)

class ProblemDetail(BaseModel):
    id: int
    title: str
    description: str
    type: str
    difficulty: int
    tags: List[str]
    category_id: int
    explanation: Optional[str] = None
    options: Optional[List[dict]] = None
    blanks: Optional[List[dict]] = None
    test_cases: List[dict] = []
    subprojects: List[dict] = []
    model_config = ConfigDict(from_attributes=True)

class AnswerResponse(BaseModel):
    answer: Optional[str] = None
    explanation: Optional[str] = None

class CategoryResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    sort_order: int
    model_config = ConfigDict(from_attributes=True)