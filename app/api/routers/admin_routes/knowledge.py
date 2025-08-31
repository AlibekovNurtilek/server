import os
from pathlib import Path

from fastapi import APIRouter, Depends, Request, HTTPException, status
from starlette.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any
from pydantic import BaseModel

from app.api.deps import get_db_session, get_current_employee, EMPLOYEE_SESSION_KEY
from app.schemas.auth_schemas import EmplyeeLoginRequest, EmplyeeOut
from app.services.admin_services.auth_service import AuthService
from app.services.customer_services.customer_service import CustomerService
from app.schemas.customer_schemas import CustomerRead, CustomerReadWithRelations
from app.db.models import EmployeeRole, Employee
from app.services.knowledge_services.about_us import AboutUsService
from app.services.knowledge_services.cards import CardsService
from app.services.knowledge_services.deposit import DepositService
from app.services.knowledge_services.info_service import InfoService

router = APIRouter(prefix="/api/admin/knowledge", tags=["knowledge"])
KNOWLEDGE_BASE_DIR = Path(os.getenv("KNOWLEDGE_BASE_DIR", "knowledge"))
about_us_service = AboutUsService(base_dir=KNOWLEDGE_BASE_DIR)
card_service = CardsService(base_dir=KNOWLEDGE_BASE_DIR)
deposit_service = DepositService(base_dir=KNOWLEDGE_BASE_DIR)
info_service = InfoService(base_dir=KNOWLEDGE_BASE_DIR)

class AboutUsRequest(BaseModel):
    about_us: dict
class CardsRequest(BaseModel):
    cards: dict

@router.get("/{lang}/about-us")
#@router.get("/about-us")
async def get_about_us(lang: str = "ky"):
    """
    Получает содержимое about-us.json для указанного языка.
    По умолчанию lang='ky'.
    """
    try:
        return await about_us_service.get_about_us(lang)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера, {lang}, {about_us_service.base_dir}")

@router.patch("/{lang}/about-us")
#@router.patch("/about-us")
async def update_about_us(lang: str = "ky", data: AboutUsRequest = None):
    """
    Обновляет содержимое about-us.json для указанного языка.
    По умолчанию lang='ky'.
    """
    if data is None:
        raise HTTPException(status_code=400, detail="Тело запроса не может быть пустым")
    
    try:
        return await about_us_service.update_about_us(lang, data.dict())
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")
    








@router.get("/{lang}/cards")
#@router.get("/cards")
async def get_cards(lang: str = "ky"):
    """
    Получает содержимое about-us.json для указанного языка.
    По умолчанию lang='ky'.
    """
    try:
        return await card_service.get_all_cards(lang)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера")
    
    
@router.get("{lang}/cards/{card_name}")
#@router.get("/cards/{card_name}")
async def get_card(lang: str, card_name: str):
    try:
        return await card_service.get_card(lang, card_name=card_name)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера")

@router.patch("{lang}/cards/{card_name}")
#@router.patch("cards/{card_name}")
async def update_card(lang: str, card_name: str, data: dict):
    try:
        return await card_service.update_card(lang, card_name=card_name, data=data)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера")
    








@router.get("/{lang}/deposits")
#@router.get("/deposits")
async def get_deposits(lang: str = "ky"):
    """
    Получает содержимое deposits.json для указанного языка.
    По умолчанию lang='ky'.
    """
    try:
        return await deposit_service.get_all_deposits(lang)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера")
    
    
@router.get("/{lang}/deposits/{deposit_name}")
#@router.get("/deposits/{deposit_name}")
async def get_deposit(lang: str, deposit_name: str):
    try:
        return await deposit_service.get_deposit(lang, deposit_name=deposit_name)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера")

@router.patch("/{lang}/deposits/{deposit_name}")
#@router.patch("/deposits/{deposit_name}")
async def update_deposit(lang: str, deposit_name: str, data: dict):
    try:
        return await deposit_service.update_deposit(lang, deposit_name=deposit_name, data=data)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера")
    


@router.get("/{lang}/info/categories")
async def get_info_categories(lang: str = "ky") -> List[str]:
    """
    Получает список всех категорий из useful-info.json для указанного языка.
    По умолчанию lang='ky'.
    """
    try:
        return await info_service.get_categories(lang)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")

@router.get("/{lang}/info/{category}")
async def get_paginated_items(lang: str, category: str, page: int = 1, page_size: int = 10) -> Dict[str, Any]:
    """
    Получает элементы указанной категории с пагинацией для указанного языка.
    По умолчанию lang='ky', page=1, page_size=10.
    """
    try:
        return await info_service.get_paginated_items(lang, category, page, page_size)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")

@router.patch("/{lang}/info/{category}/{item_id}")
async def update_item(lang: str, category: str, item_id: int, data: dict) -> dict:
    """
    Обновляет элемент в указанной категории для указанного языка (заглушка).
    По умолчанию lang='ky'.
    """
    try:
        return await info_service.update_item(lang, category, item_id, data)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")