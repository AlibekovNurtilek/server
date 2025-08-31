import json
import logging
from pathlib import Path
from fastapi import HTTPException

logger = logging.getLogger(__name__)

class AboutUsService:
    def __init__(self, base_dir: Path, filename: str = "about-us.json"):
        self.base_dir = base_dir
        self.filename = filename

    def _get_file_path(self, lang: str) -> Path:
        """Формирует путь к файлу для указанного языка."""
        if lang not in ["ky", "ru"]:
            logger.error(f"Недопустимый язык: {lang}")
            raise HTTPException(status_code=400, detail="Язык должен быть 'ky' или 'ru'")
        return self.base_dir / lang / self.filename

    async def get_about_us(self, lang: str) -> dict:
        """Читает содержимое about-us.json для указанного языка."""
        file_path = self._get_file_path(lang)
        logger.debug(f"Чтение файла: {file_path}")

        if not file_path.exists():
            logger.error(f"Файл не найден: {file_path}")
            raise HTTPException(status_code=404, detail=f"Файл {self.filename} для языка {lang} не найден")

        try:
            with open(file_path, "r", encoding="utf-8") as file:
                data = json.load(file)
                if "about_us" not in data:
                    logger.error(f"Некорректная структура файла: {file_path}")
                    raise HTTPException(status_code=422, detail="Файл не содержит ключ 'about_us'")
                return data
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка парсинга JSON в файле {file_path}: {str(e)}")
            raise HTTPException(status_code=500, detail="Ошибка при чтении файла")
        except Exception as e:
            logger.error(f"Неизвестная ошибка при чтении файла {file_path}: {str(e)}")
            raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")


    async def update_about_us(self, lang: str, data: dict) -> dict:
        """Обновляет содержимое about-us.json для указанного языка."""
        if "about_us" not in data:
            logger.error(f"Входящие данные не содержат ключ 'about-us'")
            raise HTTPException(status_code=400, detail="Тело запроса должно содержать ключ 'about_us'")

        file_path = self._get_file_path(lang)
        logger.debug(f"Обновление файла: {file_path}")

        try:
            # Создаём директорию, если не существует
            file_path.parent.mkdir(parents=True, exist_ok=True)
            # Записываем новый JSON
            with open(file_path, "w", encoding="utf-8") as file:
                json.dump(data, file, ensure_ascii=False, indent=2)
            logger.info(f"Файл успешно обновлён: {file_path}")
            return {"status": "success"}
        except Exception as e:
            logger.error(f"Ошибка при записи файла {file_path}: {str(e)}")
            raise HTTPException(status_code=500, detail="Ошибка при обновлении файла")