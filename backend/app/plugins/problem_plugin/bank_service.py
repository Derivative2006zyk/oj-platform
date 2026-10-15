"""题库导入导出服务。

Day 38：仅导出。
Day 39：导入。
"""
import hashlib
import io
import json
import re
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category
from app.models.image import Image
from app.models.problem import Problem
from app.models.research_subproject import ResearchSubproject
from app.models.test_case import TestCase


FORMAT_NAME = "oj-platform-bank"
FORMAT_VERSION = 1

# 匹配 Markdown 图片语法 ![...](url)
MD_IMAGE_RE = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")

# 匹配 /api/images/N 或 /api/image/N
IMAGE_URL_RE = re.compile(r"^/api/image(?:s)?/(\d+)(?:\?.*)?$")


def _extract_image_ids_from_text(text: Optional[str]) -> List[int]:
    """从 Markdown 文本中提取图片 ID（去重）。"""
    if not text:
        return []
    ids: List[int] = []
    for m in MD_IMAGE_RE.finditer(text):
        url = m.group(1).strip()
        mm = IMAGE_URL_RE.match(url)
        if mm:
            img_id = int(mm.group(1))
            if img_id not in ids:
                ids.append(img_id)
    return ids


def _rewrite_image_urls(text: Optional[str], id_to_name: dict) -> Optional[str]:
    """把 /api/images/N 替换为 images/{name}。"""
    if not text:
        return text

    def repl(m: re.Match) -> str:
        url = m.group(1).strip()
        mm = IMAGE_URL_RE.match(url)
        if not mm:
            return m.group(0)
        img_id = int(mm.group(1))
        new_path = id_to_name.get(img_id)
        if not new_path:
            return m.group(0)
        return f"![](images/{new_path})"

    return MD_IMAGE_RE.sub(repl, text)


def _file_hash(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def _resolve_image_path(file_path: str, upload_dir: Path) -> Optional[Path]:
    """将 image.file_path 解析为实际存在的文件路径。

    目录按 uploads/{年}/{月}/ 组织，因此优先递归查找同名文件。
    """
    p = Path(file_path)
    name = p.name

    # 1. 绝对路径直接尝试
    if p.is_absolute():
        try:
            if p.exists() and p.is_file():
                return p
        except Exception:
            pass

    # 2. upload_dir 下常见位置
    candidates = [
        upload_dir / name,
        upload_dir / "images" / name,
        upload_dir / "submissions" / name,
        upload_dir / "bank" / name,
    ]
    if not p.is_absolute():
        candidates.insert(0, upload_dir / p)

    for c in candidates:
        try:
            if c.exists() and c.is_file():
                return c
        except Exception:
            continue

    # 3. 兜底：递归查找（覆盖 uploads/{年}/{月}/ 结构）
    try:
        for found in upload_dir.rglob(name):
            if found.is_file():
                return found
    except Exception:
        pass

    return None

async def export_bank(
    db: AsyncSession,
    problem_ids: Optional[List[int]] = None,
    bank_id: Optional[int] = None,
) -> bytes:
    """导出题库为 ZIP 字节流。

    problem_ids 为 None 或空列表时导出全部。
    """
    from app.core.config import settings

    upload_dir = Path(settings.UPLOAD_DIR)

    # 1. 查询题目
    q = select(Problem)
    if problem_ids:
        q = q.where(Problem.id.in_(problem_ids))
    elif bank_id is not None:
        q = q.where(Problem.bank_id == bank_id)
    q = q.order_by(Problem.id)
    problems = list((await db.execute(q)).scalars().all())

    if not problems:
        raise ValueError("No problems to export")

    pids = [p.id for p in problems]

    # 2. 查询测试用例
    tc_res = await db.execute(
        select(TestCase).where(TestCase.problem_id.in_(pids)).order_by(TestCase.id)
    )
    test_cases_map: dict = {}
    for tc in tc_res.scalars().all():
        test_cases_map.setdefault(tc.problem_id, []).append(tc)

    # 3. 查询子项目
    sp_res = await db.execute(
        select(ResearchSubproject)
        .where(ResearchSubproject.problem_id.in_(pids))
        .order_by(ResearchSubproject.sort_order)
    )
    subprojects_map: dict = {}
    for sp in sp_res.scalars().all():
        subprojects_map.setdefault(sp.problem_id, []).append(sp)

    # 4. 收集所有图片 ID
    image_ids: set = set()
    for p in problems:
        for i in _extract_image_ids_from_text(p.description):
            image_ids.add(i)
        for i in _extract_image_ids_from_text(p.answer):
            image_ids.add(i)
        for i in _extract_image_ids_from_text(p.explanation):
            image_ids.add(i)
    for sp_list in subprojects_map.values():
        for sp in sp_list:
            for i in _extract_image_ids_from_text(sp.description):
                image_ids.add(i)
            for i in _extract_image_ids_from_text(sp.answer_guide):
                image_ids.add(i)

    # 5. 加载图片记录，计算 hash，建立映射
    id_to_name: dict = {}
    image_files: dict = {}  # zip 内文件名 -> 源文件 Path

    if image_ids:
        img_res = await db.execute(select(Image).where(Image.id.in_(list(image_ids))))
        for img in img_res.scalars().all():
            src = _resolve_image_path(img.file_path, upload_dir)
            if src is None:
                continue
            try:
                h = _file_hash(src)
            except Exception:
                continue
            ext = Path(img.file_name).suffix or ".bin"
            name = f"{h}{ext}"
            id_to_name[img.id] = name
            image_files[name] = src

    # 6. 组装分类
    cat_res = await db.execute(select(Category).order_by(Category.sort_order))
    all_cats = {c.id: c for c in cat_res.scalars().all()}
    from app.models.bank import Bank
    bank_res = await db.execute(select(Bank))
    all_banks = {b.id: b for b in bank_res.scalars().all()}

    used_cat_ids = {p.category_id for p in problems}
    categories_payload = []
    for cid in sorted(used_cat_ids):
        c = all_cats.get(cid)
        if c:
            categories_payload.append({
                "name": c.name,
                "description": c.description,
                "sort_order": c.sort_order,
            })

    # 7. 组装题目
    problems_payload = []
    for p in problems:
        cat = all_cats.get(p.category_id)
        cat_name = cat.name if cat else ""

        bank = all_banks.get(p.bank_id) if p.bank_id else None
        bank_name = bank.name if bank else ""

        payload = {
            "title": p.title,
            "category_name": cat_name,
            "bank_name": bank_name,
            "type": p.type,
            "difficulty": p.difficulty,
            "tags": p.tags or [],
            "description": _rewrite_image_urls(p.description, id_to_name),
            "answer": _rewrite_image_urls(p.answer, id_to_name),
            "explanation": _rewrite_image_urls(p.explanation, id_to_name),
            "options": p.options,
            "blanks": p.blanks,
            "test_cases": [],
            "subprojects": [],
        }

        for tc in test_cases_map.get(p.id, []):
            payload["test_cases"].append({
                "input_data": tc.input_data,
                "expected_output": tc.expected_output,
                "is_example": tc.is_example,
            })

        for sp in subprojects_map.get(p.id, []):
            payload["subprojects"].append({
                "title": sp.title,
                "description": _rewrite_image_urls(sp.description, id_to_name),
                "hint": sp.hint,
                "reference_links": sp.reference_links or [],
                "answer_guide": _rewrite_image_urls(sp.answer_guide, id_to_name),
                "sort_order": sp.sort_order,
            })

        problems_payload.append(payload)

    # 8. manifest
    used_bank_ids = {p.bank_id for p in problems if p.bank_id}
    banks_payload = []
    for bid in sorted(used_bank_ids):
        b = all_banks.get(bid)
        if b:
            banks_payload.append({
                "name": b.name,
                "description": b.description,
                "sort_order": b.sort_order,
            })

    manifest = {
        "format": FORMAT_NAME,
        "format_version": FORMAT_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "app_version": "0.2.0",
        "problem_count": len(problems_payload),
        "image_count": len(image_files),
        "categories": categories_payload,
        "banks": banks_payload,
        "problems": problems_payload,
    }

    # 9. 打包
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(
            "manifest.json",
            json.dumps(manifest, ensure_ascii=False, indent=2),
        )
        for name, src in image_files.items():
            zf.write(src, arcname=f"images/{name}")

    return buf.getvalue()