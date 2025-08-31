from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.db.models import Employee
from app.db.repositories.employee_repository import EmployeeRepository
from app.services.security import hash_password, verify_password

class AuthService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = EmployeeRepository(session)


    async def validate_login(self, *, username: str, password: str) ->Employee:
        user = await self.repo.get_by_username(username.lower())
        if not user or not verify_password(password, user.password_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")
        return user
