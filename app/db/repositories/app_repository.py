from typing import List, Tuple, Optional
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import LoanApplication, LoanApplicationStatus, CardApplication, CardApplicationStatus


class LoanApplicationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(self, page: int = 1, page_size: int = 10) -> Tuple[List[LoanApplication], int]:
        """
        Получить все заявки на кредиты с пагинацией.
        Сортировка по дате создания (сначала старые).
        """
        offset = (page - 1) * page_size

        stmt = (
            select(LoanApplication)
            .order_by(LoanApplication.created_at.asc())  # ASC → сначала старые
            .offset(offset)
            .limit(page_size)
        )
        result = await self.session.execute(stmt)
        applications = result.scalars().all()

        count_stmt = select(func.count()).select_from(LoanApplication)
        total_result = await self.session.execute(count_stmt)
        total = total_result.scalar_one()

        return applications, total

    async def update_status(self, application_id: int, new_status: LoanApplicationStatus) -> Optional[LoanApplication]:
        stmt = (
            update(LoanApplication)
            .where(LoanApplication.id == application_id)
            .values(status=new_status)
            .returning(LoanApplication)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()


class CardApplicationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(self, page: int = 1, page_size: int = 10) -> Tuple[List[CardApplication], int]:
        """
        Получить все заявки на карты с пагинацией.
        Сортировка по дате создания (сначала старые).
        """
        offset = (page - 1) * page_size

        stmt = (
            select(CardApplication)
            .order_by(CardApplication.created_at.asc())  # ASC → сначала старые
            .offset(offset)
            .limit(page_size)
        )
        result = await self.session.execute(stmt)
        applications = result.scalars().all()

        count_stmt = select(func.count()).select_from(CardApplication)
        total_result = await self.session.execute(count_stmt)
        total = total_result.scalar_one()

        return applications, total

    async def update_status(self, application_id: int, new_status: CardApplicationStatus) -> Optional[CardApplication]:
        stmt = (
            update(CardApplication)
            .where(CardApplication.id == application_id)
            .values(status=new_status)
            .returning(CardApplication)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
