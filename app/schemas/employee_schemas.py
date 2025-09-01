from pydantic import BaseModel
from pydantic import BaseModel, constr, EmailStr
from datetime import datetime
from typing import List

from app.db.models import  EmployeeRole

# Pydantic Schemas
class EmployeeRead(BaseModel):
    id: int
    username: str
    role: EmployeeRole
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # Замените orm_mode на это

class EmployeeCreate(BaseModel):
    username: constr(min_length=3, max_length=50)
    password: constr(min_length=4)

class PaginatedEmployees(BaseModel):
    items: List[EmployeeRead]
    page: int
    page_size: int
    total: int