from typing import List, Optional
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Employee

class EmployeeRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, employee_id: int) -> Optional[Employee]:
        """
        Retrieve an employee by their ID.
        
        :param employee_id: The ID of the employee.
        :return: Employee object or None if not found.
        """
        res = await self.session.execute(select(Employee).where(Employee.id == employee_id))
        return res.scalar_one_or_none()

    async def get_by_username(self, username: str) -> Optional[Employee]:
        """
        Retrieve an employee by their username.
        
        :param username: The username of the employee.
        :return: Employee object or None if not found.
        """
        res = await self.session.execute(select(Employee).where(Employee.username == username))
        return res.scalar_one_or_none()

    async def add(self, employee: Employee) -> Employee:
        """
        Add a new employee to the database.
        
        :param employee: The Employee object to add.
        :return: The added Employee object.
        """
        self.session.add(employee)
        await self.session.commit()
        return employee

    async def get_all_employees(self, limit: int = 10, offset: int = 0) -> List[Employee]:
        """
        Retrieve all employees with pagination.
        
        :param limit: Number of records to return.
        :param offset: Number of records to skip.
        :return: List of Employee objects.
        """
        stmt = select(Employee).order_by(Employee.id).offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def delete(self, employee_id: int) -> bool:
        """
        Delete an employee by their ID.
        
        :param employee_id: The ID of the employee to delete.
        :return: True if the employee was deleted, False if not found.
        """
        stmt = delete(Employee).where(Employee.id == employee_id)
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount > 0