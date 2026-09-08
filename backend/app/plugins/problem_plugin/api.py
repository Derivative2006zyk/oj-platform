from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import async_session
from app.models.problem import Problem
from app.plugins.problem_plugin import service
from app.schemas.problem import AnswerResponse, CategoryResponse

router = APIRouter(prefix="/api", tags=["problems"])

async def get_db():
    async with async_session() as session:
        yield session

@router.get("/categories", response_model=list[CategoryResponse])
async def get_categories(db: AsyncSession = Depends(get_db)):
    return await service.get_all_categories(db)

@router.get("/problems")
async def list_problems(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    category_id: int = Query(None),
    difficulty: int = Query(None, ge=1, le=5),
    type: str = Query(None),
    tag: str = Query(None),
    keyword: str = Query(None),
    db: AsyncSession = Depends(get_db)
):
    return await service.get_problem_list(
        db, page, page_size, category_id, difficulty, type, tag, keyword
    )

@router.get("/problem/{problem_id}/answer", response_model=AnswerResponse)
async def get_answer(problem_id: int, db: AsyncSession = Depends(get_db)):
    problem = await db.get(Problem, problem_id)
    if not problem:
        raise HTTPException(status_code=404, detail="题目不存在")
    return {"answer": problem.answer, "explanation": problem.explanation}

@router.get("/tag")
async def get_tags(db: AsyncSession = Depends(get_db)):
    return await service.get_all_tags(db)