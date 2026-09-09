from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import async_session
from app.models.problem import Problem
from app.plugins.problem_plugin import service
from app.schemas.problem import AnswerResponse, CategoryResponse
from app.core.security import verify_admin_key
from app.schemas.problem import ProblemCreate, ProblemUpdate

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

# 管理员接口

@router.post("/admin/problems", status_code=201)
async def create_problem(
    data: ProblemCreate,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_admin_key)
):
    """创建题目，需要管理员密钥"""
    problem = await service.create_problem(db, data)
    return {"id": problem.id, "message": "创建成功"}

@router.put("/admin/problems/{problem_id}")
async def update_problem(
    problem_id: int,
    data: ProblemUpdate,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_admin_key)
):
    """更新题目，需要管理员密钥"""
    problem = await service.update_problem(db, problem_id, data)
    if not problem:
        raise HTTPException(status_code=404, detail="题目不存在")
    return {"id": problem.id, "message": "更新成功"}

@router.delete("/admin/problems/{problem_id}")
async def delete_problem(
    problem_id: int,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_admin_key)
):
    """删除题目，需要管理员密钥"""
    success = await service.delete_problem(db, problem_id)
    if not success:
        raise HTTPException(status_code=404, detail="题目不存在")
    return {"message": "删除成功"}