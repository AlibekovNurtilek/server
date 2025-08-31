import json
import logging
from pathlib import Path
from fastapi import HTTPException
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

class SystemPromptsService:
    def __init__(self, base_dir: Path, filename: str = "system_prompts.json"):
        self.base_dir = base_dir
        self.filename = filename

    def _get_file_path(self, lang: str) -> Path:
        """Формирует путь к файлу для указанного языка."""
        if lang not in ["ky", "ru"]:
            logger.error(f"Недопустимый язык: {lang}")
            raise HTTPException(status_code=400, detail="Язык должен быть 'ky' или 'ru'")
        return self.base_dir / lang / self.filename

    async def get_available_prompts(self, lang: str) -> List[str]:
        """Возвращает список доступных ключей промптов в system_prompts.json для указанного языка."""
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
                    raise HTTPException(status_code=422, detail="Файл должен содержать объект с ключами промптов")
                return list(data.keys())
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка парсинга JSON в файле {file_path}: {str(e)}")
            raise HTTPException(status_code=500, detail="Ошибка при чтении файла")
        except Exception as e:
            logger.error(f"Неизвестная ошибка при чтении файла {file_path}: {str(e)}")
            raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")

    async def get_prompt(self, lang: str, prompt_key: str) -> Dict[str, Any]:
        """Возвращает конкретный промпт по его ключу для указанного языка."""
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
                    raise HTTPException(status_code=422, detail="Файл должен содержать объект с ключами промптов")

                if prompt_key not in data:
                    logger.error(f"Промпт с ключом '{prompt_key}' не найден в файле {file_path}")
                    raise HTTPException(status_code=404, detail=f"Промпт с ключом '{prompt_key}' не найден")

                return {"key": prompt_key, "template": data[prompt_key]["template"]}
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка парсинга JSON в файле {file_path}: {str(e)}")
            raise HTTPException(status_code=500, detail="Ошибка при чтении файла")
        except Exception as e:
            logger.error(f"Неизвестная ошибка при чтении файла {file_path}: {str(e)}")
            raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")

    async def update_prompt(self, lang: str, prompt_key: str, data: dict) -> dict:
        """Обновляет промпт в system_prompts.json для указанного языка по ключу."""
        if "template" not in data:
            logger.error(f"Входящие данные не содержат ключ 'template'")
            raise HTTPException(status_code=400, detail="Тело запроса должно содержать ключ 'template'")

        file_path = self._get_file_path(lang)
        logger.debug(f"Обновление файла: {file_path}")

        if not file_path.exists():
            logger.error(f"Файл не найден: {file_path}")
            raise HTTPException(status_code=404, detail=f"Файл {self.filename} для языка {lang} не найден")

        try:
            # Читаем текущий JSON
            with open(file_path, "r", encoding="utf-8") as file:
                file_data = json.load(file)
                if not isinstance(file_data, dict):
                    logger.error(f"Некорректная структура файла: {file_path}")
                    raise HTTPException(status_code=422, detail="Файл должен содержать объект с ключами промптов")

                if prompt_key not in file_data:
                    logger.error(f"Промпт с ключом '{prompt_key}' не найден в файле {file_path}")
                    raise HTTPException(status_code=404, detail=f"Промпт с ключом '{prompt_key}' не найден")

                # Обновляем шаблон промпта
                file_data[prompt_key] = {"template": data["template"]}

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