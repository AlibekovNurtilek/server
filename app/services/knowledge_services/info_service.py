import json
import logging
from pathlib import Path
from fastapi import HTTPException
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class InfoService:
    def __init__(self, base_dir: Path, filename: str = "useful-info.json"):
        self.base_dir = base_dir
        self.filename = filename

    def _get_file_path(self, lang: str) -> Path:
        """Формирует путь к файлу для указанного языка."""
        if lang not in ["ky", "ru"]:
            logger.error(f"Недопустимый язык: {lang}")
            raise HTTPException(status_code=400, detail="Язык должен быть 'ky' или 'ru'")
        return self.base_dir / lang / self.filename

    async def get_categories(self, lang: str) -> List[str]:
        """Возвращает список всех категорий из useful-info.json для указанного языка."""
        file_path = self._get_file_path(lang)
        logger.debug(f"Чтение файла для получения категорий: {file_path}")

        if not file_path.exists():
            logger.error(f"Файл не найден: {file_path}")
            raise HTTPException(status_code=404, detail=f"Файл {self.filename} для языка {lang} не найден")

        try:
            with open(file_path, "r", encoding="utf-8") as file:
                data = json.load(file)
                if "useful-info" not in data:
                    logger.error(f"Некорректная структура файла: {file_path}")
                    raise HTTPException(status_code=422, detail="Файл не содержит ключ 'useful-info'")
                return list(data["useful-info"].keys())
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка парсинга JSON в файле {file_path}: {str(e)}")
            raise HTTPException(status_code=500, detail="Ошибка при чтении файла")
        except Exception as e:
            logger.error(f"Неизвестная ошибка при чтении файла {file_path}: {str(e)}")
            raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")

    async def get_paginated_items(self, lang: str, category: str, page: int = 1, page_size: int = 10) -> Dict[str, Any]:
        """Возвращает элементы указанной категории с пагинацией."""
        file_path = self._get_file_path(lang)
        logger.debug(f"Чтение файла для категории {category}: {file_path}")

        if not file_path.exists():
            logger.error(f"Файл не найден: {file_path}")
            raise HTTPException(status_code=404, detail=f"Файл {self.filename} для языка {lang} не найден")

        try:
            with open(file_path, "r", encoding="utf-8") as file:
                data = json.load(file)
                if "useful-info" not in data:
                    logger.error(f"Некорректная структура файла: {file_path}")
                    raise HTTPException(status_code=422, detail="Файл не содержит ключ 'useful-info'")
                if category not in data["useful-info"]:
                    logger.error(f"Категория '{category}' не найдена в файле: {file_path}")
                    raise HTTPException(status_code=404, detail=f"Категория '{category}' не найдена")

                items = data["useful-info"][category]
                total_items = len(items)
                total_pages = (total_items + page_size - 1) // page_size

                if page < 1 or page > total_pages:
                    logger.error(f"Недопустимый номер страницы: {page}")
                    raise HTTPException(status_code=400, detail=f"Номер страницы должен быть от 1 до {total_pages}")

                start_idx = (page - 1) * page_size
                end_idx = start_idx + page_size
                paginated_items = items[start_idx:end_idx]

                return {
                    "category": category,
                    "items": paginated_items,
                    "page": page,
                    "total": total_items,
                    "page_size": page_size,
                    
                }
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка парсинга JSON в файле {file_path}: {str(e)}")
            raise HTTPException(status_code=500, detail="Ошибка при чтении файла")
        except Exception as e:
            logger.error(f"Неизвестная ошибка при чтении файла {file_path}: {str(e)}")
            raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")

    async def update_item(self, lang: str, category: str, item_id: int, data: dict) -> dict:
        """Обновляет элемент в указанной категории для указанного языка."""
        file_path = self._get_file_path(lang)
        logger.debug(f"Обновление файла для категории {category}, элемента {item_id}: {file_path}")

        if not file_path.exists():
            logger.error(f"Файл не найден: {file_path}")
            raise HTTPException(status_code=404, detail=f"Файл {self.filename} для языка {lang} не найден")

        # Читаем текущий файл
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                current_data = json.load(file)
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка парсинга JSON в файле {file_path}: {str(e)}")
            raise HTTPException(status_code=500, detail="Ошибка при чтении файла")
        except Exception as e:
            logger.error(f"Неизвестная ошибка при чтении файла {file_path}: {str(e)}")
            raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")

        # Проверяем наличие ключа 'useful-info' и категории
        if "useful-info" not in current_data:
            logger.error(f"Некорректная структура файла: {file_path}")
            raise HTTPException(status_code=422, detail="Файл не содержит ключ 'useful-info'")
        if category not in current_data["useful-info"]:
            logger.error(f"Категория '{category}' не найдена в файле: {file_path}")
            raise HTTPException(status_code=404, detail=f"Категория '{category}' не найдена")

        # Ищем элемент с указанным item_id
        items = current_data["useful-info"][category]
        item_index = next((i for i, item in enumerate(items) if item.get("id") == item_id), None)
        if item_index is None:
            logger.error(f"Элемент с id {item_id} не найден в категории {category}")
            raise HTTPException(status_code=404, detail=f"Элемент с id {item_id} не найден в категории {category}")

        # Проверяем, что входящие данные содержат обязательные поля
        if "question" not in data or "answer" not in data:
            logger.error(f"Входящие данные не содержат обязательные поля 'question' или 'answer'")
            raise HTTPException(status_code=400, detail="Тело запроса должно содержать поля 'question' и 'answer'")

        # Формируем обновленный элемент, сохраняя id
        updated_item = {
            "id": item_id,
            "question": data["question"],
            "answer": data["answer"]
        }

        # Обновляем элемент в списке
        current_data["useful-info"][category][item_index] = updated_item

        # Сохраняем обновленный JSON
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as file:
                json.dump(current_data, file, ensure_ascii=False, indent=2)
            logger.info(f"Файл успешно обновлён: {file_path}")
            return {"status": "success", "updated_item": updated_item}
        except Exception as e:
            logger.error(f"Ошибка при записи файла {file_path}: {str(e)}")
            raise HTTPException(status_code=500, detail="Ошибка при обновлении файла")