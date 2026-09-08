from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.category import Category
from app.models.problem import Problem
from app.models.test_case import TestCase
from app.models.research_subproject import ResearchSubproject
from app.schemas.problem import ProblemCreate, ProblemUpdate

async def get_all_categories(db: AsyncSession):
    """获取所有分类，按照 sort_order 排序"""
    result = await db.execute(select(Category).order_by(Category.sort_order))
    return result.scalars().all()

async def get_problem_list(
        db: AsyncSession,
        page: int = 1,
        page_size: int = 10,
        category_id: int = None,
        difficulty: int = None,
        type: str = None,
        tag: str = None,
        keyword: str = None
):
    """获取题目列表，带筛选和分页"""
    query = select(Problem)
    if category_id:
        query = query.where(Problem.category_id == category_id)
    if difficulty:
        query = query.where(Problem.difficulty == difficulty)
    if type:
        query = query.where(Problem.type == type)
    if tag:
        query = query.where(Problem.tags.contains([tag]))
    if keyword:
        query = query.where(Problem.title(f"%{keyword}%"))

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar

    query = query.order_by(Problem.id.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    problem = result.scalars().all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items" : problem
    }

async def get_problem_detail(db: AsyncSession, problem_id: int):
    """获取题目详情，根据不同题型加载不同题目数据结构"""
    problem = await db.get(Problem, problem_id)
    if not problem:
        return None
    detail = {
        "id": problem_id,
        "title": problem.title,
        "description": problem.description,
        "type": problem.type,
        "difficulty": problem.difficulty,
        "tags": problem.tags,
        "category_id": problem.category_id,
        "explanation": problem.explanation,
        "options": problem.options,
        "blanks": problem.blanks,
        "test_cases": [],
        "subprojects": []
    }
    if problem.type == "algorithm":
        result = await db.execute(
            select(TestCase).where(TestCase.problem_id == problem_id, TestCase.is_example == True)
        )
        detail["test_cases"] = [
            {"input_data": tc.input_data, "expected_output": tc.expected_output}
            for tc in result.scalars().all()
        ]
    if problem.type == "research":
        result = await db.execute(
            select(ResearchSubproject)
            .where(ResearchSubproject.problem_id == problem_id)
            .order_by(ResearchSubproject.sort_order)
        )
        detail["subprojects"] = [
            {
                "id": sp.id,
                "title": sp.title,
                "description": sp.description,
                "hint": sp.hint,
                "reference_links": sp.reference_links,
                "answer_guide": sp.answer_guide,
                "sort_order": sp.sort_order
            }
            for sp in result.scalars().all()
        ]
    return detail

async def get_all_tags(db: AsyncSession):
    """获取所有不重复的标签列表"""
    result = await db.execute(select(Problem.tags))
    all_tags = set()
    for row in result.scalars().all():
        if row:
            all_tags.update(row)

    return sorted(list(all_tags))