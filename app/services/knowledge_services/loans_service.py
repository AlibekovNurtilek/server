import json
import logging
from pathlib import Path
from fastapi import HTTPException
from typing import List, Dict, Any

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

    async def get_loan_product_names(self, lang: str) -> List[Dict[str, str]]:
        """Возвращает список словарей с type и name из loan_products для указанного языка."""
        file_path = self._get_file_path(lang)
        logger.debug(f"Чтение файла для получения type и name loan_products: {file_path}")

        if not file_path.exists():
            logger.error(f"Файл не найден: {file_path}")
            raise HTTPException(status_code=404, detail=f"Файл {self.filename} для языка {lang} не найден")

        try:
            with open(file_path, "r", encoding="utf-8") as file:
                data = json.load(file)
                if "loan_products" not in data:
                    logger.error(f"Некорректная структура файла: {file_path}")
                    raise HTTPException(status_code=422, detail="Файл не содержит ключ 'loan_products'")
                return [{"type": product["type"], "name": product["name"]} for product in data["loan_products"]]
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка парсинга JSON в файле {file_path}: {str(e)}")
            raise HTTPException(status_code=500, detail="Ошибка при чтении файла")
        except Exception as e:
            logger.error(f"Неизвестная ошибка при чтении файла {file_path}: {str(e)}")
            raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")

    async def get_loan_product_by_type(self, lang: str, product_type: str) -> Dict[str, Any]:
        """Возвращает объект loan_product по заданному type для указанного языка."""
        file_path = self._get_file_path(lang)
        logger.debug(f"Чтение файла для поиска loan_product по типу '{product_type}': {file_path}")

        if not file_path.exists():
            logger.error(f"Файл не найден: {file_path}")
            raise HTTPException(status_code=404, detail=f"Файл {self.filename} для языка {lang} не найден")

        try:
            with open(file_path, "r", encoding="utf-8") as file:
                data = json.load(file)
                if "loan_products" not in data:
                    logger.error(f"Некорректная структура файла: {file_path}")
                    raise HTTPException(status_code=422, detail="Файл не содержит ключ 'loan_products'")
                
                for product in data["loan_products"]:
                    if product.get("type") == product_type:
                        return product
                
                logger.error(f"Продукт с типом '{product_type}' не найден в файле {file_path}")
                raise HTTPException(status_code=404, detail=f"Продукт с типом '{product_type}' не найден")
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка парсинга JSON в файле {file_path}: {str(e)}")
            raise HTTPException(status_code=500, detail="Ошибка при чтении файла")
        except Exception as e:
            logger.error(f"Неизвестная ошибка при чтении файла {file_path}: {str(e)}")
            raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")
    
    
    async def update_loan_product(self, lang: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Обновляет объект loan_product по типу для указанного языка."""
        file_path = self._get_file_path(lang)
        logger.debug(f"Обновление loan_product в файле {file_path}")

        if not data or "type" not in data:
            logger.error("Данные или поле 'type' отсутствуют в запросе")
            raise HTTPException(status_code=400, detail="Тело запроса должно содержать поле 'type'")

        product_type = data["type"]
        
        if not file_path.exists():
            logger.error(f"Файл не найден: {file_path}")
            raise HTTPException(status_code=404, detail=f"Файл {self.filename} для языка {lang} не найден")

        try:
            with open(file_path, "r", encoding="utf-8") as file:
                file_data = json.load(file)
                
            if "loan_products" not in file_data:
                logger.error(f"Некорректная структура файла: {file_path}")
                raise HTTPException(status_code=422, detail="Файл не содержит ключ 'loan_products'")

            found = False
            for i, product in enumerate(file_data["loan_products"]):
                if product.get("type") == product_type:
                    file_data["loan_products"][i] = data
                    found = True
                    break

            if not found:
                logger.warning(f"Продукт с типом '{product_type}' не найден в файле {file_path}")
                raise HTTPException(status_code=404, detail=f"Продукт с типом '{product_type}' не найден")

            with open(file_path, "w", encoding="utf-8") as file:
                json.dump(file_data, file, ensure_ascii=False, indent=2)
            
            logger.info(f"Продукт с типом '{product_type}' успешно обновлен в файле {file_path}")
            return data

        except json.JSONDecodeError as e:
            logger.error(f"Ошибка парсинга JSON в файле {file_path}: {str(e)}")
            raise HTTPException(status_code=500, detail="Ошибка при чтении файла: неверный формат JSON")
        except IOError as e:
            logger.error(f"Ошибка записи в файл {file_path}: {str(e)}")
            raise HTTPException(status_code=500, detail="Ошибка при записи в файл")
        except Exception as e:
            logger.error(f"Неизвестная ошибка при обновлении файла {file_path}: {str(e)}")
            raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера при обновлении файла")