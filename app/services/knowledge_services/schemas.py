import json
import logging
from pathlib import Path
from fastapi import HTTPException
from typing import Dict, List

logger = logging.getLogger(__name__)

class SchemasService:
    def __init__(self, base_dir: Path, filename: str = "schemas.json"):
        self.base_dir = base_dir
        self.filename = filename

    def _get_file_path(self, lang: str) -> Path:
        """Формирует путь к файлу для указанного языка."""
        if lang not in ["ky", "ru"]:
            logger.error(f"Недопустимоый язык: {lang}")
            raise HTTPException(status_code=400, detail="Язык должен быть 'ky' или 'ru'")
        return self.base_dir / lang / self.filename

    async def get_schemas(self, lang: str, page: int = 1, page_size: int = 10) -> Dict[str, any]:
        """Читает содержимое schemas.json для указанного языка с пагинацией."""
        file_path = self._get_file_path(lang)
        logger.debug(f"Чтение файла: {file_path}")

        if not file_path.exists():
            logger.error(f"Файл не найден: {file_path}")
            raise HTTPException(status_code=404, detail=f"Файл {self.filename} для языка {lang} не найден")

        try:
            with open(file_path, "r", encoding="utf-8") as file:
                data = json.load(file)
                if not isinstance(data, dict):
                    logger.error(f"Некорректная структура файла: {file_path}")
                    raise HTTPException(status_code=422, detail="Файл должен содержать объект с ключами схем")

                # Извлекаем только name и description для каждой схемы
                schemas = [
                    {"name": schema_data["name"], "description": schema_data["description"]}
                    for schema_data in data.values()
                    if "name" in schema_data and "description" in schema_data
                ]

                # Пагинация
                total_items = len(schemas)
                start = (page - 1) * page_size
                end = start + page_size
                paginated_schemas = schemas[start:end]

                return {
                    "schemas": paginated_schemas,
                    "total": total_items,
                    "page": page,
                    "page_size": page_size
                }
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка парсинга JSON в файле {file_path}: {str(e)}")
            raise HTTPException(status_code=500, detail="Ошибка при чтении файла")
        except Exception as e:
            logger.error(f"Неизвестная ошибка при чтении файла {file_path}: {str(e)}")
            raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")
        
    async def update_schema(self, lang: str, data: dict) -> dict:
        """Обновляет запись в schemas.json для указанного языка по имени схемы."""
        if "name" not in data or "description" not in data:
            logger.error(f"Входящие данные не содержат ключ 'name' или 'description'")
            raise HTTPException(status_code=400, detail="Тело запроса должно содержать ключи 'name' и 'description'")

        file_path = self._get_file_path(lang)
        logger.debug(f"Обновление файла: {file_path}")

        # Проверяем существование файла
        if not file_path.exists():
            logger.error(f"Файл не найден: {file_path}")
            raise HTTPException(status_code=404, detail=f"Файл {self.filename} для языка {lang} не найден")

        try:
            # Читаем текущий JSON
            with open(file_path, "r", encoding="utf-8") as file:
                file_data = json.load(file)
                if not isinstance(file_data, dict):
                    logger.error(f"Некорректная структура файла: {file_path}")
                    raise HTTPException(status_code=422, detail="Файл должен содержать объект с ключами схем")

            # Ищем схему по name
            target_name = data["name"]
            schema_key = None
            for key, schema_data in file_data.items():
                if schema_data.get("name") == target_name:
                    schema_key = key
                    break

            if schema_key is None:
                logger.error(f"Схема с name '{target_name}' не найдена в файле {file_path}")
                raise HTTPException(status_code=404, detail=f"Схема с name '{target_name}' не найдена")

            # Обновляем данные схемы, сохраняя существующие поля (например, parameters)
            file_data[schema_key] = {
                **file_data[schema_key],  # Сохраняем все существующие поля
                "name": data["name"],
                "description": data["description"]
            }

            # Создаём директорию, если не существует
            file_path.parent.mkdir(parents=True, exist_ok=True)
            # Записываем обновлённый JSON
            with open(file_path, "w", encoding="utf-8") as file:
                json.dump(file_data, file, ensure_ascii=False, indent=2)
            logger.info(f"Файл успешно обновлён: {file_path}")
            return {"status": "success"}

        except json.JSONDecodeError as e:
            logger.error(f"Ошибка парсинга JSON в файле {file_path}: {str(e)}")
            raise HTTPException(status_code=500, detail="Ошибка при чтении файла")
        except Exception as e:
            logger.error(f"Ошибка при записи файла {file_path}: {str(e)}")
            raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")
            
        