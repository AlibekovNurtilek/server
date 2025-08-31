import json
import logging
from pathlib import Path
from fastapi import HTTPException

logger = logging.getLogger(__name__)

class CardsService:
    def __init__(self, base_dir: Path, filename: str = "cards.json"):
        self.base_dir = base_dir
        self.filename = filename

    def _get_file_path(self, lang: str) -> Path:
        """Формирует путь к файлу для указанного языка."""
        if lang not in ["ky", "ru"]:
            logger.error(f"Недопустимый язык: {lang}")
            raise HTTPException(status_code=400, detail="Язык должен быть 'ky' или 'ru'")
        return self.base_dir / lang / self.filename

    async def get_all_cards(self, lang: str) -> dict:
        """Читает названия всех карт из cards.json для указанного языка."""
        file_path = self._get_file_path(lang)
        logger.debug(f"Чтение файла: {file_path}")

        if not file_path.exists():
            logger.error(f"Файл не найден: {file_path}")
            raise HTTPException(status_code=404, detail=f"Файл {self.filename} для языка {lang} не найден")

        try:
            with open(file_path, "r", encoding="utf-8") as file:
                data = json.load(file)
                if "cards" not in data:
                    logger.error(f"Некорректная структура файла: {file_path}")
                    raise HTTPException(status_code=422, detail="Файл не содержит ключ 'cards'")
                # Извлекаем только названия карт
                card_names = {key: value["name"] for key, value in data["cards"].items()}
                return {"cards": card_names}
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка парсинга JSON в файле {file_path}: {str(e)}")
            raise HTTPException(status_code=500, detail="Ошибка при чтении файла")
        except Exception as e:
            logger.error(f"Неизвестная ошибка при чтении файла {file_path}: {str(e)}")
            raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")

    async def get_card(self, lang: str, card_name: str) -> dict:
        """Читает информацию о конкретной карте из cards.json для указанного языка."""
        file_path = self._get_file_path(lang)
        logger.debug(f"Чтение файла для карты {card_name}: {file_path}")

        if not file_path.exists():
            logger.error(f"Файл не найден: {file_path}")
            raise HTTPException(status_code=404, detail=f"Файл {self.filename} для языка {lang} не найден")

        try:
            with open(file_path, "r", encoding="utf-8") as file:
                data = json.load(file)
                if "cards" not in data:
                    logger.error(f"Некорректная структура файла: {file_path}")
                    raise HTTPException(status_code=422, detail="Файл не содержит ключ 'cards'")
                if card_name not in data["cards"]:
                    logger.error(f"Карта '{card_name}' не найдена в файле: {file_path}")
                    raise HTTPException(status_code=404, detail=f"Карта '{card_name}' не найдена")
                return {card_name: data["cards"][card_name]}
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка парсинга JSON в файле {file_path}: {str(e)}")
            raise HTTPException(status_code=500, detail="Ошибка при чтении файла")
        except Exception as e:
            logger.error(f"Неизвестная ошибка при чтении файла {file_path}: {str(e)}")
            raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")

    async def update_card(self, lang: str, card_name: str, data: dict) -> dict:
        """Обновляет информацию о конкретной карте в cards.json для указанного языка."""
        file_path = self._get_file_path(lang)
        logger.debug(f"Обновление файла для карты {card_name}: {file_path}")

        # Проверяем, что входящие данные содержат ключ, соответствующий card_name
        if card_name not in data:
            logger.error(f"Входящие данные не содержат ключ '{card_name}'")
            raise HTTPException(status_code=400, detail=f"Тело запроса должно содержать ключ '{card_name}'")

        # Читаем текущий файл, если существует
        current_data = {"cards": {}}
        if file_path.exists():
            try:
                with open(file_path, "r", encoding="utf-8") as file:
                    current_data = json.load(file)
                if "cards" not in current_data:
                    logger.error(f"Некорректная структура существующего файла: {file_path}")
                    raise HTTPException(status_code=422, detail="Существующий файл не содержит ключ 'cards'")
            except json.JSONDecodeError as e:
                logger.error(f"Ошибка парсинга JSON в файле {file_path}: {str(e)}")
                raise HTTPException(status_code=500, detail="Ошибка при чтении файла")
            
        # Проверяем, существует ли карта в текущих данных
        if card_name not in current_data["cards"]:
            logger.error(f"Карта {card_name} не найдена в файле {file_path}")
            raise HTTPException(status_code=404, detail=f"Карта '{card_name}' не существует")

        # Проверяем, что в данных есть поле "name"
        if "name" not in data[card_name]:
            logger.error(f"Входящие данные для карты {card_name} не содержат ключ 'name'")
            raise HTTPException(status_code=400, detail="Тело запроса должно содержать ключ 'name' для карты")

        # Обновляем данные для указанной карты
        current_data["cards"][card_name] = data[card_name]

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