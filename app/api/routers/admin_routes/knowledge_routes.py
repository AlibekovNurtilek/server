import os
from pathlib import Path

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from pydantic import BaseModel

from app.services.knowledge_services.about_us import AboutUsService
from app.services.knowledge_services.cards import CardsService
from app.services.knowledge_services.deposit import DepositService
from app.services.knowledge_services.info_service import InfoService
from app.services.knowledge_services.schemas import SchemasService
from app.services.knowledge_services.system_prompts_service import SystemPromptsService
from app.services.knowledge_services.loans_service import LoansService

KNOWLEDGE_BASE_DIR = Path(os.getenv("KNOWLEDGE_BASE_DIR", "knowledge"))

about_us_service = AboutUsService(base_dir=KNOWLEDGE_BASE_DIR)
card_service = CardsService(base_dir=KNOWLEDGE_BASE_DIR)
deposit_service = DepositService(base_dir=KNOWLEDGE_BASE_DIR)
info_service = InfoService(base_dir=KNOWLEDGE_BASE_DIR)
schemas_service = SchemasService(base_dir=KNOWLEDGE_BASE_DIR)
system_prompts_service = SystemPromptsService(base_dir=KNOWLEDGE_BASE_DIR)
loans_service = LoansService(base_dir=KNOWLEDGE_BASE_DIR)


class AboutUsRequest(BaseModel):
    about_us: dict
class CardsRequest(BaseModel):
    cards: dict
    
router = APIRouter(prefix="/api/admin/knowledge", tags=["knowledge"])

@router.get("/about-us")
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

@router.patch("/about-us")
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
    








@router.get("/cards")
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
    
    
@router.get("/cards/{card_name}")
async def get_card(lang: str, card_name: str):
    try:
        return await card_service.get_card(lang, card_name=card_name)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера")

@router.patch("/cards/{card_name}")
async def update_card(lang: str, card_name: str, data: dict):
    try:
        return await card_service.update_card(lang, card_name=card_name, data=data)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера")
    








@router.get("/deposits")
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
    
    
@router.get("/deposits/{deposit_name}")
async def get_deposit(lang: str, deposit_name: str):
    try:
        return await deposit_service.get_deposit(lang, deposit_name=deposit_name)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера")

@router.patch("/deposits/{deposit_name}")
async def update_deposit(lang: str, deposit_name: str, data: dict):
    try:
        return await deposit_service.update_deposit(lang, deposit_name=deposit_name, data=data)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера")
    


@router.get("/info/categories")
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

@router.get("/info/{category}")
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

@router.patch("/info/{category}/{item_id}")
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
    






@router.get("/schemas")
async def get_schemas(lang: str = "ky", page: int = 1, page_size: int = 10) -> Dict[str, Any]:
    """
    Получает содержимое schemas.json для указанного языка с пагинацией.
    По умолчанию lang='ky', page=1, page_size=10.
    """
    try:
        return await schemas_service.get_schemas(lang, page, page_size)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")


@router.patch("/schemas")
async def update_schema(lang: str = "ky", data: dict = None) -> dict:
    """
    Обновляет запись в schemas.json для указанного языка по имени схемы.
    По умолчанию lang='ky'.
    """
    if data is None:
        raise HTTPException(status_code=400, detail="Тело запроса не может быть пустым")
    
    try:
        return await schemas_service.update_schema(lang, data)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")
    



@router.get("/prompts")
async def get_available_prompts(lang: str = "ky") -> List[str]:
    """
    Получает список доступных ключей промптов из system_prompts.json для указанного языка.
    По умолчанию lang='ky'.
    """
    try:
        return await system_prompts_service.get_available_prompts(lang)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")

@router.get("/prompts/{prompt_key}")
async def get_prompt(lang: str = "ky", prompt_key: str = None) -> Dict[str, Any]:
    """
    Получает конкретный промпт по ключу из system_prompts.json для указанного языка.
    По умолчанию lang='ky'.
    """
    try:
        return await system_prompts_service.get_prompt(lang, prompt_key)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")

@router.patch("/prompts/{prompt_key}")
async def update_prompt(lang: str = "ky", prompt_key: str = None, data: dict = None) -> dict:
    """
    Обновляет промпт в system_prompts.json для указанного языка по ключу.
    По умолчанию lang='ky'.
    """
    if data is None:
        raise HTTPException(status_code=400, detail="Тело запроса не может быть пустым")
    
    try:
        return await system_prompts_service.update_prompt(lang, prompt_key, data)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")