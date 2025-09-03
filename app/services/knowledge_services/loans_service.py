import json
import logging
from pathlib import Path
from fastapi import HTTPException

logger = logging.getLogger(__name__)

class LoansService:
    def __init__(self, base_dir: Path, filename: str = "loans.json"):
        self.base_dir = base_dir
        self.filename = filename

    def _get_file_path(self, lang: str) -> Path:
        """Формирует путь к файлу для указанного языка."""
        if lang not in ["ky", "ru"]:
            logger.error(f"Недопустимый язык: {lang}")
            raise HTTPException(status_code=400, detail="Язык должен быть 'ky' или 'ru'")
        return self.base_dir / lang / self.filename