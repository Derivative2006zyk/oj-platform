"""题库导入服务。

处理 ZIP：
- 解析 manifest.json
- 按名称匹配/创建分类和题库
- 冲突处理：skip / rename / overwrite
- 图片按内容 sha256 去重
"""
import base64
import hashlib
import io
import json
import re
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.bank import Bank
from app.models.category import Category
from app.models.image import Image
from app.models.problem import Problem
from app.models.research_subproject import ResearchSubproject
from app.models.test_case import TestCase


FORMAT_NAME = "oj-platform-bank"

# 匹配 images/xxx.ext
IMAGES_PATH_RE = re.compile(r"images/([A-Za-z0-9_]+\.[A-Za-z0-9]+)")


def _sha256_16(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()[:16]


def _extract_referenced_images(text: Optional[str]) -> list:
    if not text:
        return []
    return IMAGES_PATH_RE.findall(text)


def _rewrite_images_to_api(text: Optional[str], name_to_id: dict) -> Optional[str]:
    """把 images/xxx.ext 替换为 /api/images/N。"""
    if not text:
        return text

    def repl(m: re.Match) -> str:
        name = m.group(1)
        img_id = name_to_id.get(name)
        if img_id is None:
            return m.group(0)
        return f"/api/images/{img_id}"

    return IMAGES_PATH_RE.sub(repl, text)


async def _resolve_or_create_category(
    db: AsyncSession, name: str, cache: dict
) -> Optional[int]:
    if not name:
        return None
    if name in cache:
        return cache[name]

    res = await db.execute(select(Category).where(Category.name == name))
    cat = res.scalar_one_or_none()
    if cat is None:
        cat = Category(name=name, description=None, sort_order=0)
        db.add(cat)
        await db.flush()
    cache[name] = cat.id
    return cat.id


async def _resolve_or_create_bank(
    db: AsyncSession, name: str, cache: dict
) -> Optional[int]:
    if not name:
        return None
    if name in cache:
        return cache[name]

    res = await db.execute(select(Bank).where(Bank.name == name))
    bank = res.scalar_one_or_none()
    if bank is None:
        bank = Bank(name=name, description=None, sort_order=0)
        db.add(bank)
        await db.flush()
    cache[name] = bank.id
    return bank.id


async def _title_exists(db: AsyncSession, title: str) -> bool:
    res = await db.execute(select(Problem).where(Problem.title == title))
    return res.scalar_one_or_none() is not None


async def _unique_title(db: AsyncSession, base: str) -> str:
    """生成一个不冲突的标题。"""
    if not await _title_exists(db, base):
        return base
    i = 1
    while i < 1000:
        candidate = f"{base} (导入{i})"
        if not await _title_exists(db, candidate):
            return candidate
        i += 1
    return f"{base} (导入{9999})"


def _guess_mime(ext: str) -> str:
    e = ext.lower()
    if e == ".png":
        return "image/png"
    if e in (".jpg", ".jpeg"):
        return "image/jpeg"
    if e == ".webp":
        return "image/webp"
    if e == ".gif":
        return "image/gif"
    return "application/octet-stream"


async def _process_images(
    db: AsyncSession,
    zf: zipfile.ZipFile,
    all_names: list,
    upload_dir: Path,
) -> dict:
    """处理 ZIP 内 images/ 目录，返回 {zip内文件名: 图片ID}。"""
    name_to_id: dict = {}
    if not all_names:
        return name_to_id

    now = datetime.now()
    target_dir = upload_dir / f"{now.year:04d}" / f"{now.month:02d}"
    target_dir.mkdir(parents=True, exist_ok=True)

    for name in all_names:
        try:
            data = zf.read(f"images/{name}")
        except KeyError:
            continue

        h = _sha256_16(data)
        ext = Path(name).suffix or ".bin"
        stored_name = f"{h}{ext}"

        # 按 file_name 查找已存在的图片
        res = await db.execute(select(Image).where(Image.file_name == stored_name))
        existing = res.scalar_one_or_none()

        if existing is not None:
            name_to_id[name] = existing.id
            continue

        target = target_dir / stored_name
        target.write_bytes(data)

        img = Image(
            problem_id=None,
            file_name=stored_name,
            file_path=str(target),
            file_size=len(data),
            mime_type=_guess_mime(ext),
            upload_by="bank_import",
        )
        db.add(img)
        await db.flush()
        name_to_id[name] = img.id

    return name_to_id


async def import_bank(
    db: AsyncSession,
    file_bytes: bytes,
    conflict_strategy: str = "skip",
) -> dict:
    """导入题库 ZIP。"""
    from app.core.config import settings

    if conflict_strategy not in ("skip", "rename", "overwrite"):
        raise ValueError(f"Unknown conflict_strategy: {conflict_strategy}")

    try:
        zf = zipfile.ZipFile(io.BytesIO(file_bytes))
    except zipfile.BadZipFile:
        raise ValueError("Not a valid ZIP file")

    try:
        manifest_data = zf.read("manifest.json")
    except KeyError:
        raise ValueError("manifest.json not found in ZIP")

    try:
        manifest = json.loads(manifest_data)
    except json.JSONDecodeError:
        raise ValueError("manifest.json is not valid JSON")

    if manifest.get("format") != FORMAT_NAME:
        raise ValueError(f"Unsupported format: {manifest.get('format')}")

    problems_in = manifest.get("problems") or []
    if not isinstance(problems_in, list):
        raise ValueError("manifest.problems must be a list")

    upload_dir = Path(settings.UPLOAD_DIR)

    # 收集所有 images/xxx 引用
    image_names: set = set()
    for p in problems_in:
        for field in ("description", "answer", "explanation"):
            for n in _extract_referenced_images(p.get(field)):
                image_names.add(n)
        for sp in p.get("subprojects") or []:
            for field in ("description", "answer_guide"):
                for n in _extract_referenced_images(sp.get(field)):
                    image_names.add(n)

    name_to_id = await _process_images(db, zf, list(image_names), upload_dir)

    cat_cache: dict = {}
    bank_cache: dict = {}

    imported = 0
    skipped = 0
    failed = 0
    errors: list = []
    new_ids: list = []

    for item in problems_in:
        try:
            title = (item.get("title") or "").strip()
            if not title:
                failed += 1
                errors.append("Problem with empty title skipped")
                continue

            final_title = title
            if await _title_exists(db, title):
                if conflict_strategy == "skip":
                    skipped += 1
                    continue
                elif conflict_strategy == "rename":
                    final_title = await _unique_title(db, title)
                elif conflict_strategy == "overwrite":
                    res = await db.execute(
                        select(Problem).where(Problem.title == title)
                    )
                    for old in res.scalars().all():
                        await db.delete(old)
                    await db.flush()

            cat_id = await _resolve_or_create_category(
                db, item.get("category_name") or "", cat_cache
            ) or 1
            bank_id = await _resolve_or_create_bank(
                db, item.get("bank_name") or "", bank_cache
            )

            description = _rewrite_images_to_api(item.get("description"), name_to_id)
            answer = _rewrite_images_to_api(item.get("answer"), name_to_id)
            explanation = _rewrite_images_to_api(item.get("explanation"), name_to_id)

            problem = Problem(
                title=final_title,
                category_id=cat_id,
                bank_id=bank_id,
                description=description or "",
                type=item.get("type") or "algorithm",
                difficulty=item.get("difficulty") or 1,
                tags=item.get("tags") or [],
                answer=answer,
                explanation=explanation,
                options=item.get("options"),
                blanks=item.get("blanks"),
            )
            db.add(problem)
            await db.flush()

            for tc in item.get("test_cases") or []:
                db.add(
                    TestCase(
                        problem_id=problem.id,
                        input_data=tc.get("input_data") or "",
                        expected_output=tc.get("expected_output") or "",
                        is_example=bool(tc.get("is_example", True)),
                    )
                )

            for sp in item.get("subprojects") or []:
                db.add(
                    ResearchSubproject(
                        problem_id=problem.id,
                        title=sp.get("title") or "",
                        description=_rewrite_images_to_api(
                            sp.get("description"), name_to_id
                        ) or "",
                        hint=sp.get("hint"),
                        reference_links=sp.get("reference_links") or [],
                        answer_guide=_rewrite_images_to_api(
                            sp.get("answer_guide"), name_to_id
                        ),
                        sort_order=sp.get("sort_order") or 0,
                    )
                )

            await db.commit()
            imported += 1
            new_ids.append(problem.id)
        except Exception as e:
            await db.rollback()
            failed += 1
            errors.append(str(e))

    return {
        "total": len(problems_in),
        "imported": imported,
        "skipped": skipped,
        "failed": failed,
        "problem_ids": new_ids,
        "errors": errors[:20],
    }