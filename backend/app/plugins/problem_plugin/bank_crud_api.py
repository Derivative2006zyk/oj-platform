"""题库 CRUD API。"""
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import verify_admin_key
from app.database import get_db
from app.plugins.problem_plugin import bank_crud_service
from app.schemas.bank import BankCreate, BankUpdate, BankResponse, BankWithCount


router = APIRouter(prefix="/api", tags=["banks"])


@router.get("/banks", response_model=List[BankWithCount])
async def list_banks(db: AsyncSession = Depends(get_db)):
    return await bank_crud_service.list_banks(db)


@router.post(
    "/admin/banks",
    status_code=201,
    response_model=BankResponse,
)
async def create_bank(
    data: BankCreate,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_admin_key),
):
    return await bank_crud_service.create_bank(db, data)


@router.put("/admin/banks/{bank_id}", response_model=BankResponse)
async def update_bank(
    bank_id: int,
    data: BankUpdate,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_admin_key),
):
    bank = await bank_crud_service.update_bank(db, bank_id, data)
    if not bank:
        raise HTTPException(status_code=404, detail="Bank not found")
    return bank


@router.delete("/admin/banks/{bank_id}")
async def delete_bank(
    bank_id: int,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_admin_key),
):
    success = await bank_crud_service.delete_bank(db, bank_id)
    if not success:
        raise HTTPException(status_code=404, detail="Bank not found")
    return {"message": "deleted"}