import asyncio
import json
import logging
import time
from typing import Dict, Any, Optional, AsyncGenerator
import httpx

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

class AitilLLMProxy:
    def __init__(
        self,
        *,
        llm_url: str = "http://127.0.0.1:11434/v1/chat/completions;",  # Замени на http://127.0.0.1:11434/v1/chat/completions для локальной Ollama
        model: str = "aitil",
        temperature: float = 0.5,
        default_language: str = "ky",
        request_timeout: Optional[float] = 60.0,
    ) -> None:
        self.llm_url = llm_url
        self.model = model
        self.temperature = temperature
        self.default_language = default_language
        self.request_timeout = request_timeout

    async def _build_payload(
        self,
        message: str,
        language: str,
        stream: bool = True,
    ) -> Dict[str, Any]:
        """Формирует payload для запроса к LLM."""
        # Длинный системный промпт
        system_prompt = """
        Ты - умный ассистент, созданный для помощи пользователям на кыргызском языке.
        Твоя задача - предоставлять точные, полезные и подробные ответы, учитывая контекст запроса.
        Используй профессиональный, но дружелюбный тон. Если запрос связан с финансовыми услугами,
        предоставляй информацию о продуктах банка, таких как кредиты, депозиты, переводы и т.д.
        Убедись, что ответы соответствуют кыргызскому законодательству и нормам банковской деятельности.
        Если пользователь запрашивает что-то специфичное, уточняй детали, чтобы дать максимально релевантный ответ.
        Все ответы должны быть на кыргызском языке, если не указано иное.
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message}
        ]

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "stream": stream,
            "max_tokens": 2000,
        }
        logger.info("LLM request payload: %s", json.dumps(payload, ensure_ascii=False, indent=2))
        return payload

    async def stream_answer(self, message: str, language: str = "ky") -> AsyncGenerator[bytes, None]:
        """Стримит ответ от LLM по байтам и логирует время получения чанков."""
        payload = await self._build_payload(message=message, language=language)
        
        headers = {
            "Accept": "text/event-stream",
            "Content-Type": "application/json",
            "Cache-Control": "no-cache"
        }
        timeout = httpx.Timeout(self.request_timeout)
        
        async with httpx.AsyncClient(timeout=timeout) as client:
            try:
                async with client.stream("POST", self.llm_url, json=payload, headers=headers) as resp:
                    resp.raise_for_status()
                    last_time = time.time()
                    async for chunk in resp.aiter_bytes():
                        current_time = time.time()
                        time_diff = current_time - last_time
                        logger.info(f"Time since last chunk: {time_diff:.2f} seconds")
                        # Пытаемся декодировать для отображения в консоли
                        try:
                            decoded_chunk = chunk.decode("utf-8", errors="replace")
                            logger.info(f"Received chunk (decoded): {decoded_chunk}")
                        except UnicodeDecodeError:
                            logger.info(f"Received chunk (raw bytes): {chunk}")
                        print(f"Streamed chunk (raw bytes): {chunk}")
                        print(f"Streamed chunk (decoded): {decoded_chunk if 'decoded_chunk' in locals() else 'Failed to decode'}")
                        yield chunk
                        last_time = current_time
            except httpx.HTTPStatusError as e:
                error_message = f"data: {{\"error\": \"API error: {e.response.status_code}\"}}"
                logger.error(error_message)
                yield error_message.encode("utf-8")
                return
            except Exception as e:
                error_message = f"data: {{\"error\": \"Stream error: {str(e)}\"}}"
                logger.error(error_message)
                yield error_message.encode("utf-8")
                return

async def main():
    # Создаем клиент
    client = AitilLLMProxy(
        llm_url="https://chat.aitil.kg/suroo",  # Замени на http://127.0.0.1:11434/v1/chat/completions для локальной Ollama
        model="aitil",
        temperature=0.5,
        default_language="ky",
        request_timeout=60.0
    )

    # Длинное пользовательское сообщение
    user_message = """
    Саламатсызбы! Мен банктык кызматтар жөнүндө маалымат алгым келет.
    Сиздерде кандай кредиттик программалар бар? Мисалы, ипотека, авто кредит,
    же жеке муктаждыктар үчүн кредиттер барбы? Алардын пайыздык чендери кандай?
    Ошондой эле, депозиттик программалар жөнүндө айтып бере аласызбы?
    Мисалы, кандай мөөнөттөр жана пайыздар бар? Эгерде мен чет өлкөгө акча
    которууну кааласам, кандай варианттар бар жана алардын баасы кандай?
    Мындан тышкары, банктык эсеп ачуу үчүн кандай документтер керек?
    Жоопту кыргыз тилинде жана мүмкүн болушунча толук бериңиз.
    """

    # Стриминг ответа
    async for chunk in client.stream_answer(user_message, language="ky"):
        pass  # Чанки уже выводятся в консоль через print в stream_answer

if __name__ == "__main__":
    asyncio.run(main())