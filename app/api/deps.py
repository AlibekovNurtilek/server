from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.base import get_session
from typing import Optional
from app.db.repositories.customer_repository import CustomerRepository
from app.db.repositories.employee_repository import EmployeeRepository

SESSION_KEY = "user_id"
EMPLOYEE_SESSION_KEY = "employee_id"

async def get_db_session():
    async for s in get_session():
        yield s

async def get_current_customer(request: Request, session: AsyncSession = Depends(get_db_session)):
    uid = request.session.get(SESSION_KEY)
    if not uid:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    user = await CustomerRepository(session).get_by_id(int(uid))
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user

async def get_optional_customer(
    request: Request,
    session: AsyncSession = Depends(get_db_session),
):
    uid = request.session.get(SESSION_KEY)
    if not uid:
        return None
    user = await CustomerRepository(session).get_by_id(int(uid))
    return user 

async def get_current_employee(request: Request, session: AsyncSession = Depends(get_db_session)):
    employee_data = request.session.get(EMPLOYEE_SESSION_KEY)
    if not employee_data or not isinstance(employee_data, dict) or "id" not in employee_data or "role" not in employee_data:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Employee authentication required")
    employee = await EmployeeRepository(session).get_by_id(int(employee_data["id"]))
    if not employee:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Employee not found")
    if employee.role.value != employee_data["role"]:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid employee role")
    return employee
