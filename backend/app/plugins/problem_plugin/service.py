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

async def create_problem(db: AsyncSession, data: ProblemCreate):
    """
    创建题目，根据题型插入关联数据（测试用例或子项目）
    """
    problem = Problem(
        title=data.title,
        category_id=data.category_id,
        description=data.description,
        type=data.type,
        difficulty=data.difficulty,
        tags=data.tags,
        answer=data.answer,
        explanation=data.explanation,
        options=data.options,
        blanks=data.blanks,
    )
    db.add(problem)
    await db.flush()

    if data.type == "algorithm":
        for tc in data.test_cases:
            db.add(TestCase(
                problem_id=problem.id,
                input_data=tc.input_data,
                expected_output=tc.expected_output,
                is_example=tc.is_example
            ))

    if data.type == "research":
        for sp in data.subprojects:
            db.add(ResearchSubproject(
                problem_id=problem.id,
                title=sp.title,
                description=sp.description,
                hint=sp.hint,
                reference_links=sp.reference_links,
                answer_guide=sp.answer_guide,
                sort_order=sp.sort_order
            ))

    await db.commit()
    await db.refresh(problem)
    return problem

async def update_problem(db: AsyncSession, problem_id: int, data: ProblemUpdate):
    """
    更新题目，支持部分更新。如果提供了 test_cases 或 subprojects，则先删除旧的再插入新的。
    """
    problem = await db.get(Problem, problem_id)
    if not problem:
        return None

    update_data = data.model_dump(exclude_unset=True)
    test_cases_data = update_data.pop("test_cases", None)
    subprojects_data = update_data.pop("subprojects", None)

    for field, value in update_data.items():
        setattr(problem, field, value)

    if test_cases_data is not None:
        await db.execute(delete(TestCase).where(TestCase.problem_id == problem_id))
        for tc in test_cases_data:
            db.add(TestCase(
                problem_id=problem_id,
                input_data=tc["input_data"],
                expected_output=tc["expected_output"],
                is_example=tc.get("is_example", True)
            ))

    if subprojects_data is not None:
        await db.execute(delete(ResearchSubproject).where(ResearchSubproject.problem_id == problem_id))
        for sp in subprojects_data:
            db.add(ResearchSubproject(
                problem_id=problem_id,
                title=sp["title"],
                description=sp["description"],
                hint=sp.get("hint"),
                reference_links=sp.get("reference_links", []),
                answer_guide=sp.get("answer_guide"),
                sort_order=sp.get("sort_order", 0)
            ))

    await db.commit()
    await db.refresh(problem)
    return problem

async def delete_problem(db: AsyncSession, problem_id: int):
    """
    删除题目，数据库会级联删除测试用例、子项目、图片（如果设置了外键级联）
    """
    problem = await db.get(Problem, problem_id)
    if not problem:
        return False

    await db.delete(problem)
    await db.commit()
    return True