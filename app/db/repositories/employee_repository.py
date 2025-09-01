from typing import List, Optional, Tuple
from sqlalchemy import select, delete, func
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

    async def get_all_employees(self, page: int = 1, page_size: int = 10) -> Tuple[List[Employee], int]:
        """
        Retrieve all employees with pagination.

        :param page: Page number (1-based).
        :param page_size: Number of records per page.
        :return: Tuple of (list of Employee objects, total count).
        """
        offset = (page - 1) * page_size
        # Query for employees
        stmt = select(Employee).order_by(Employee.id).offset(offset).limit(page_size)
        result = await self.session.execute(stmt)
        employees = result.scalars().all()
        
        # Query for total count
        count_stmt = select(func.count()).select_from(Employee)
        total_result = await self.session.execute(count_stmt)
        total = total_result.scalar_one()
        
        return employees, total
    
    async def delete(self, employee_id: int) -> bool:
        """
        Delete an employee by their ID.

        :param employee_id: The ID of the employee to delete.
        :return: True if the employee was found and deleted, False otherwise.
        """
        employee = await self.get_by_id(employee_id)
        if not employee:
            return False

        await self.session.delete(employee)
        await self.session.commit()
        return True