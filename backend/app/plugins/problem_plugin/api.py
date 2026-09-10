from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import async_session
from app.models.problem import Problem
from app.plugins.problem_plugin import service
from app.schemas.problem import (
    AnswerResponse,
    CategoryResponse,
    ProblemCreate,
    ProblemUpdate,
)
from app.core.security import verify_admin_key

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
    db: AsyncSession = Depends(get_db),
):
    return await service.get_problem_list(
        db, page, page_size, category_id, difficulty, type, tag, keyword
    )

@router.get("/problems/{problem_id}")
async def get_problem(problem_id: int, db: AsyncSession = Depends(get_db)):
    detail = await service.get_problem_detail(db, problem_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Problem not found")
    return detail

@router.get("/problems/{problem_id}/answer", response_model=AnswerResponse)
async def get_answer(problem_id: int, db: AsyncSession = Depends(get_db)):
    problem = await db.get(Problem, problem_id)
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")
    return {"answer": problem.answer, "explanation": problem.explanation}

@router.get("/tags")
async def get_tags(db: AsyncSession = Depends(get_db)):
    return await service.get_all_tags(db)

@router.post("/admin/problems", status_code=201)
async def create_problem(
    data: ProblemCreate,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_admin_key),
):
    problem = await service.create_problem(db, data)
    return {"id": problem.id, "message": "created"}


@router.put("/admin/problems/{problem_id}")
async def update_problem(
    problem_id: int,
    data: ProblemUpdate,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_admin_key),
):
    problem = await service.update_problem(db, problem_id, data)
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")
    return {"id": problem.id, "message": "updated"}


@router.delete("/admin/problems/{problem_id}")
async def delete_problem(
    problem_id: int,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_admin_key),
):
    success = await service.delete_problem(db, problem_id)
    if not success:
        raise HTTPException(status_code=404, detail="Problem not found")
    return {"message": "deleted"}