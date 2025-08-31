import json
import logging
from pathlib import Path
from fastapi import HTTPException

logger = logging.getLogger(__name__)

class DepositService:
    def __init__(self, base_dir: Path, filename: str = "deposits.json"):
        self.base_dir = base_dir
        self.filename = filename

    def _get_file_path(self, lang: str) -> Path:
        """Формирует путь к файлу для указанного языка."""
        if lang not in ["ky", "ru"]:
            logger.error(f"Недопустимый язык: {lang}")
            raise HTTPException(status_code=400, detail="Язык должен быть 'ky' или 'ru'")
        return self.base_dir / lang / self.filename

    async def get_all_deposits(self, lang: str) -> dict:
        """Читает названия всех депозитов из deposits.json для указанного языка."""
        file_path = self._get_file_path(lang)
        logger.debug(f"Чтение файла: {file_path}")

        if not file_path.exists():
            logger.error(f"Файл не найден: {file_path}")
            raise HTTPException(status_code=404, detail=f"Файл {self.filename} для языка {lang} не найден")

        try:
            with open(file_path, "r", encoding="utf-8") as file:
                data = json.load(file)
                if "deposits" not in data:
                    logger.error(f"Некорректная структура файла: {file_path}")
                    raise HTTPException(status_code=422, detail="Файл не содержит ключ 'deposits'")
                # Извлекаем только названия депозитов
                deposit_names = {key: value["name"] for key, value in data["deposits"].items()}
                return {"deposits": deposit_names}
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка парсинга JSON в файле {file_path}: {str(e)}")
            raise HTTPException(status_code=500, detail="Ошибка при чтении файла")
        except Exception as e:
            logger.error(f"Неизвестная ошибка при чтении файла {file_path}: {str(e)}")
            raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")

    async def get_deposit(self, lang: str, deposit_name: str) -> dict:
        """Читает информацию о конкретном депозите из deposits.json для указанного языка."""
        file_path = self._get_file_path(lang)
        logger.debug(f"Чтение файла для депозита {deposit_name}: {file_path}")

        if not file_path.exists():
            logger.error(f"Файл не найден: {file_path}")
            raise HTTPException(status_code=404, detail=f"Файл {self.filename} для языка {lang} не найден")

        try:
            with open(file_path, "r", encoding="utf-8") as file:
                data = json.load(file)
                if "deposits" not in data:
                    logger.error(f"Некорректная структура файла: {file_path}")
                    raise HTTPException(status_code=422, detail="Файл не содержит ключ 'deposits'")
                if deposit_name not in data["deposits"]:
                    logger.error(f"Депозит '{deposit_name}' не найден в файле: {file_path}")
                    raise HTTPException(status_code=404, detail=f"Депозит '{deposit_name}' не найден")
                return {deposit_name: data["deposits"][deposit_name]}
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка парсинга JSON в файле {file_path}: {str(e)}")
            raise HTTPException(status_code=500, detail="Ошибка при чтении файла")
        except Exception as e:
            logger.error(f"Неизвестная ошибка при чтении файла {file_path}: {str(e)}")
            raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")

    async def update_deposit(self, lang: str, deposit_name: str, data: dict) -> dict:
        """Обновляет информацию о конкретном депозите в deposits.json для указанного языка."""
        file_path = self._get_file_path(lang)
        logger.debug(f"Обновление файла для депозита {deposit_name}: {file_path}")

        # Проверяем, что входящие данные содержат ключ, соответствующий deposit_name
        if deposit_name not in data:
            logger.error(f"Входящие данные не содержат ключ '{deposit_name}'")
            raise HTTPException(status_code=400, detail=f"Тело запроса должно содержать ключ '{deposit_name}'")

        # Читаем текущий файл, если существует
        current_data = {"deposits": {}}
        if file_path.exists():
            try:
                with open(file_path, "r", encoding="utf-8") as file:
                    current_data = json.load(file)
                if "deposits" not in current_data:
                    logger.error(f"Некорректная структура существующего файла: {file_path}")
                    raise HTTPException(status_code=422, detail="Существующий файл не содержит ключ 'deposits'")
            except json.JSONDecodeError as e:
                logger.error(f"Ошибка парсинга JSON в файле {file_path}: {str(e)}")
                raise HTTPException(status_code=500, detail="Ошибка при чтении файла")
            
        # Проверяем, существует ли депозит в текущих данных
        if deposit_name not in current_data["deposits"]:
            logger.error(f"Депозит {deposit_name} не найден в файле {file_path}")
            raise HTTPException(status_code=404, detail=f"Депозит '{deposit_name}' не существует")

        # Проверяем, что в данных есть поле "name"
        if "name" not in data[deposit_name]:
            logger.error(f"Входящие данные для депозита {deposit_name} не содержат ключ 'name'")
            raise HTTPException(status_code=400, detail="Тело запроса должно содержать ключ 'name' для депозита")

        # Обновляем данные для указанного депозита
        current_data["deposits"][deposit_name] = data[deposit_name]

        try:
            # Создаём директорию, если не существует
            file_path.parent.mkdir(parents=True, exist_ok=True)
            # Записываем обновленный JSON
            with open(file_path, "w", encoding="utf-8") as file:
                json.dump(current_data, file, ensure_ascii=False, indent=2)
            logger.info(f"Файл успешно обновлён: {file_path}")
            return {"status": "success"}
        except Exception as e:
            logger.error(f"Ошибка при записи файла {file_path}: {str(e)}")
            raise HTTPException(status_code=500, detail="Ошибка при обновлении файла")