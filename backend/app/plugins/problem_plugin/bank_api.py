"""题库导入导出 API。"""
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import verify_admin_key
from app.database import get_db
from app.plugins.problem_plugin import bank_service


router = APIRouter(prefix="/api", tags=["bank"])


class ExportRequest(BaseModel):
    problem_ids: Optional[List[int]] = None
    bank_id: Optional[int] = None


@router.post("/admin/bank/export")
async def export_bank(
    payload: ExportRequest,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_admin_key),
):
    """导出题库为 ZIP。problem_ids 为空时导出全部。"""
    try:
        data = await bank_service.export_bank(
            db, payload.problem_ids, payload.bank_id
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    filename = f"ojbank_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"

    return StreamingResponse(
        iter([data]),
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )

@router.post("/admin/bank/import")
async def import_bank(
    file: UploadFile = File(...),
    conflict_strategy: str = Form("skip"),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_admin_key),
):
    """导入题库 ZIP。"""
    from app.plugins.problem_plugin import bank_import_service

    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty file")

    try:
        result = await bank_import_service.import_bank(
            db, data, conflict_strategy=conflict_strategy
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return result