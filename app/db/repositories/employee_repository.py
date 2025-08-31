from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Employee

class EmployeeRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, employee_id: int) -> Optional[Employee]:
        res = await self.session.execute(select(Employee).where(Employee.id == employee_id))
        return res.scalar_one_or_none()

    async def get_by_username(self, username: str) -> Optional[Employee]:
        res = await self.session.execute(select(Employee).where(Employee.username == username))
        return res.scalar_one_or_none()