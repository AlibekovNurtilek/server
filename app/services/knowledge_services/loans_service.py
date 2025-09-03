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
    async def get_loan_application_process(self, lang: str) -> dict:
        """Читает содержимое loan_application_process из loans.json для указанного языка."""
        file_path = self._get_file_path(lang)
        logger.debug(f"Чтение файла: {file_path}")

        if not file_path.exists():
            logger.error(f"Файл не найден: {file_path}")
            raise HTTPException(status_code=404, detail=f"Файл {self.filename} для языка {lang} не найден")

        try:
            with open(file_path, "r", encoding="utf-8") as file:
                data = json.load(file)
                if "loan_application_process" not in data:
                    logger.error(f"Некорректная структура файла: {file_path}")
                    raise HTTPException(status_code=422, detail="Файл не содержит ключ 'loan_application_process'")
                return data["loan_application_process"]
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка парсинга JSON в файле {file_path}: {str(e)}")
            raise HTTPException(status_code=500, detail="Ошибка при чтении файла")
        except Exception as e:
            logger.error(f"Неизвестная ошибка при чтении файла {file_path}: {str(e)}")
            raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")

    async def update_loan_application_process(self, lang: str, loan_data: dict) -> dict:
        """Обновляет содержимое loan_application_process в loans.json для указанного языка."""
        file_path = self._get_file_path(lang)
        logger.debug(f"Обновление файла: {file_path}")

        try:
            if file_path.exists():
                with open(file_path, "r", encoding="utf-8") as file:
                    existing_data = json.load(file)
            else:
                existing_data = {}

            existing_data["loan_application_process"] = loan_data

            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as file:
                json.dump(existing_data, file, ensure_ascii=False, indent=2)
            logger.info(f"Файл успешно обновлён: {file_path}")
            return {"status": "success"}
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка парсинга JSON в файле {file_path}: {str(e)}")
            raise HTTPException(status_code=500, detail="Ошибка при чтении файла")
        except Exception as e:
            logger.error(f"Ошибка при записи файла {file_path}: {str(e)}")
            raise HTTPException(status_code=500, detail="Ошибка при обновлении файла")




    async def get_required_documents(self, lang: str) -> dict:
            """Читает содержимое required_documents из loans.json для указанного языка."""
            file_path = self._get_file_path(lang)
            logger.debug(f"Чтение файла: {file_path}")

            if not file_path.exists():
                logger.error(f"Файл не найден: {file_path}")
                raise HTTPException(status_code=404, detail=f"Файл {self.filename} для языка {lang} не найден")

            try:
                with open(file_path, "r", encoding="utf-8") as file:
                    data = json.load(file)
                    if "required_documents" not in data:
                        logger.error(f"Некорректная структура файла: {file_path}")
                        raise HTTPException(status_code=422, detail="Файл не содержит ключ 'required_documents'")
                    return data["required_documents"]
            except json.JSONDecodeError as e:
                logger.error(f"Ошибка парсинга JSON в файле {file_path}: {str(e)}")
                raise HTTPException(status_code=500, detail="Ошибка при чтении файла")
            except Exception as e:
                logger.error(f"Неизвестная ошибка при чтении файла {file_path}: {str(e)}")
                raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")

    async def update_required_documents(self, lang: str, documents_data: dict) -> dict:
        """Обновляет содержимое required_documents в loans.json для указанного языка."""
        file_path = self._get_file_path(lang)
        logger.debug(f"Обновление файла: {file_path}")

        try:
            if file_path.exists():
                with open(file_path, "r", encoding="utf-8") as file:
                    existing_data = json.load(file)
            else:
                existing_data = {}

            existing_data["required_documents"] = documents_data

            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as file:
                json.dump(existing_data, file, ensure_ascii=False, indent=2)
            logger.info(f"Файл успешно обновлён: {file_path}")
            return {"status": "success"}
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка парсинга JSON в файле {file_path}: {str(e)}")
            raise HTTPException(status_code=500, detail="Ошибка при чтении файла")
        except Exception as e:
            logger.error(f"Ошибка при записи файла {file_path}: {str(e)}")
            raise HTTPException(status_code=500, detail="Ошибка при обновлении файла")            