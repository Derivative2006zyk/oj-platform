"""题库 CRUD 服务。"""
from typing import List, Optional

from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.bank import Bank
from app.models.problem import Problem
from app.schemas.bank import BankCreate, BankUpdate


async def list_banks(db: AsyncSession) -> List[dict]:
    """返回题库列表，带题目数量。"""
    result = await db.execute(
        select(Bank).order_by(Bank.sort_order, Bank.id)
    )
    banks = result.scalars().all()

    count_res = await db.execute(
        select(Problem.bank_id, func.count()).group_by(Problem.bank_id)
    )
    counts = {bid: cnt for bid, cnt in count_res.all()}

    return [
        {
            "id": b.id,
            "name": b.name,
            "description": b.description,
            "sort_order": b.sort_order,
            "created_at": b.created_at,
            "problem_count": counts.get(b.id, 0),
        }
        for b in banks
    ]


async def get_bank(db: AsyncSession, bank_id: int) -> Optional[Bank]:
    return await db.get(Bank, bank_id)


async def create_bank(db: AsyncSession, data: BankCreate) -> Bank:
    bank = Bank(
        name=data.name,
        description=data.description,
        sort_order=data.sort_order,
    )
    db.add(bank)
    await db.commit()
    await db.refresh(bank)
    return bank


async def update_bank(
    db: AsyncSession, bank_id: int, data: BankUpdate
) -> Optional[Bank]:
    bank = await db.get(Bank, bank_id)
    if not bank:
        return None
    update_data = data.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        setattr(bank, k, v)
    await db.commit()
    await db.refresh(bank)
    return bank


async def delete_bank(db: AsyncSession, bank_id: int) -> bool:
    bank = await db.get(Bank, bank_id)
    if not bank:
        return False
    # 该题库下的题目 bank_id 置空
    await db.execute(
        update(Problem).where(Problem.bank_id == bank_id).values(bank_id=None)
    )
    await db.delete(bank)
    await db.commit()
    return True