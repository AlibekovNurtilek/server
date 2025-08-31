from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, HTTPException, status
from pydantic import BaseModel, constr, EmailStr
from passlib.context import CryptContext
from datetime import datetime
from app.db.models import Employee, EmployeeRole

from app.schemas.employee_schemas import EmployeeRead, EmployeeCreate
from app.db.repositories.employee_repository import EmployeeRepository


# Service
class EmployeeService:
    def __init__(self, session: AsyncSession = Depends()):
        self.repository = EmployeeRepository(session)
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    async def create(self, employee_data: EmployeeCreate) -> EmployeeRead:
        """
        Create a new employee with hashed password.
        
        :param employee_data: EmployeeCreate schema with input data.
        :return: EmployeeRead schema of the created employee.
        :raises HTTPException: If username already exists.
        """
        # Check if username already exists
        existing_employee = await self.repository.get_by_username(employee_data.username)
        if existing_employee:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists")

        # Hash the password
        password_hash = self.pwd_context.hash(employee_data.password)
        
        # Create employee instance
        employee = Employee(
            username=employee_data.username,
            password_hash=password_hash,
            role=EmployeeRole.manager
        )
        
        # Save to database
        created_employee = await self.repository.add(employee)
        return EmployeeRead.from_orm(created_employee)

    async def get_by_id(self, employee_id: int) -> EmployeeRead:
        """
        Retrieve an employee by their ID.
        
        :param employee_id: The ID of the employee.
        :return: EmployeeRead schema.
        :raises HTTPException: If employee not found.
        """
        employee = await self.repository.get_by_id(employee_id)
        if not employee:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
        return EmployeeRead.from_orm(employee)

    async def get_by_username(self, username: str) -> EmployeeRead:
        """
        Retrieve an employee by their username.
        
        :param username: The username of the employee.
        :return: EmployeeRead schema.
        :raises HTTPException: If employee not found.
        """
        employee = await self.repository.get_by_username(username)
        if not employee:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
        return EmployeeRead.from_orm(employee)



    async def delete(self, employee_id: int) -> None:
        """
        Delete an employee by their ID.
        
        :param employee_id: The ID of the employee to delete.
        :raises HTTPException: If employee not found.
        """
        success = await self.repository.delete(employee_id)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")

    async def get_all_employees(self, limit: int = 10, offset: int = 0) -> List[EmployeeRead]:
        """
        Retrieve all employees with pagination.
        
        :param limit: Number of records to return.
        :param offset: Number of records to skip.
        :return: List of EmployeeRead schemas.
        """
        employees = await self.repository.get_all_employees(limit=limit, offset=offset)
        return [EmployeeRead.from_orm(employee) for employee in employees]