"""题库导入导出 API。"""
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import verify_admin_key
from app.database import get_db
from app.plugins.problem_plugin import bank_service


router = APIRouter(prefix="/api", tags=["bank"])


class ExportRequest(BaseModel):
    problem_ids: Optional[List[int]] = None


@router.post("/admin/bank/export")
async def export_bank(
    payload: ExportRequest,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_admin_key),
):
    """导出题库为 ZIP。problem_ids 为空时导出全部。"""
    try:
        data = await bank_service.export_bank(db, payload.problem_ids)
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