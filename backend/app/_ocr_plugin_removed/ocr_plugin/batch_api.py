from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import List

from app.database import get_db
from app.core.security import require_admin
from app.models.user import User
from app.plugins.problem_plugin.service import create_problem
from app.schemas.problem import ProblemCreate

router = APIRouter(prefix="/api/plugins/ocr", tags=["ocr"])

class BatchImportItem(BaseModel):
    title: str
    description: str
    type: str
    difficulty: int
    tags: List[str]
    category_id: int = 1

class BatchImportRequest(BaseModel):
    problems: List[BatchImportItem]

@router.post("/batch-import")
async def batch_import(
    req: BatchImportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """批量导入识别出的题目"""
    imported_count = 0
    for item in req.problems:
        data = ProblemCreate(
            title=item.title,
            category_id=item.category_id,
            description=item.description,
            type=item.type,
            difficulty=item.difficulty,
            tags=item.tags,
            test_cases=[],
            subproblems=[]
        )
        await create_problem(db, data)
        imported_count += 1
        
    return {"message": "success", "imported": imported_count}