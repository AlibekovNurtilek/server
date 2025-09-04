import os
from dotenv import load_dotenv
load_dotenv()
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from app.settings import settings
from app.api.routers.user_routes import auth as auth_router, conversation as conversation_router, message as message_router, chat as chat_router
from app.api.routers.admin_routes import admin_routes, knowledge as knowledge_routes, application_routes
from fastapi import FastAPI


logging.basicConfig(
    level=logging.INFO,  # чтобы INFO был виден
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)



app = FastAPI(title="Bank Assistant API")

# ✅ Разрешаем CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080", "https://frontend-domain.com", "http://localhost:8081"],  # адреса фронта
    allow_credentials=True,  # важно для сессионных cookies
    allow_methods=["*"],     # или конкретные методы: ["GET", "POST"]
    allow_headers=["*"],     # или ["Content-Type", "Authorization"]
)

# ✅ Сессии
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.session_secret,
    session_cookie="session",
    same_site="lax",
    https_only=False if settings.debug else True
)

app.include_router(conversation_router.router)
app.include_router(auth_router.router)
app.include_router(message_router.router)
app.include_router(chat_router.router)
app.include_router(admin_routes.router)
app.include_router(knowledge_routes.router)
app.include_router(application_routes.router)

@app.get("/")
async def root():
    return {"message": "welcome"}

