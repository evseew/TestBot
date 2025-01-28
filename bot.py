import os
import openai
import logging
import asyncio
from aiogram import Bot, Dispatcher, Router, types
from aiogram.filters import Command
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Загружаем переменные из .env
load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") 
ASSISTANT_ID = os.getenv("ASSISTANT_ID")

# Проверяем, загрузились ли переменные
if not TELEGRAM_BOT_TOKEN or not OPENAI_API_KEY or not ASSISTANT_ID:
    raise ValueError("❌ Ошибка: Проверь .env файл, некоторые переменные не загружены!")

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Создаем объекты бота, диспетчера и роутера
bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher()
router = Router()

# Хранение `thread_id` и истории сообщений пользователей
user_threads = {}
user_messages = {}
MEMORY_LIMIT = 10  # Количество сообщений для хранения
MESSAGE_LIFETIME = timedelta(hours=24)  # Время жизни сообщений

async def cleanup_old_messages():
    """Очищает старые сообщения"""
    # Функция больше не нужна, но оставляем пустой для обратной совместимости
    pass

async def get_or_create_thread(user_id):
    """Получает или создает новый thread_id для пользователя."""
    if user_id in user_threads:
        return user_threads[user_id]

    thread = openai.beta.threads.create()
    thread_id = thread.id

    user_threads[user_id] = thread_id
    user_messages[user_id] = []
    return thread_id

async def add_message_to_history(user_id, role, content):
    """Добавляет сообщение в историю"""
    if user_id not in user_messages:
        user_messages[user_id] = []
    
    user_messages[user_id].append({
        'role': role,
        'content': content,
        'timestamp': datetime.now()  # Оставляем timestamp для возможного использования в будущем
    })
    
    # Ограничиваем только по количеству сообщений
    if len(user_messages[user_id]) > MEMORY_LIMIT:
        user_messages[user_id].pop(0)

async def get_conversation_context(user_id):
    """Получает контекст разговора"""
    if user_id not in user_messages:
        return ""
    
    context = "\nПредыдущий контекст разговора:\n"
    for msg in user_messages[user_id]:
        context += f"{msg['role']}: {msg['content']}\n"
    return context

async def chat_with_assistant(user_id, user_message):
    """Отправляет сообщение ассистенту и получает ответ."""
    thread_id = await get_or_create_thread(user_id)
    
    # Добавляем контекст к сообщению
    context = await get_conversation_context(user_id)
    full_message = f"{user_message}\n{context}"

    # Отправляем сообщение в поток
    openai.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=full_message
    )

    # Запускаем ассистента
    run = openai.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=ASSISTANT_ID
    )

    # Ждем завершения обработки
    while True:
        run_status = openai.beta.threads.runs.retrieve(
            thread_id=thread_id,
            run_id=run.id
        )
        if run_status.status in ["completed", "failed"]:
            break
        await asyncio.sleep(1)  # Добавляем задержку

    # Получаем ответ от ассистента
    messages = openai.beta.threads.messages.list(thread_id=thread_id)

    if messages and len(messages.data) > 0:
        response = messages.data[0].content[0].text.value
        # Сохраняем сообщения в историю
        await add_message_to_history(user_id, "user", user_message)
        await add_message_to_history(user_id, "assistant", response)
        return response

    return "Ошибка: не удалось получить ответ от ассистента."

@router.message(Command("start"))
async def start_command(message: types.Message):
    """Приветственное сообщение при старте."""
    await message.answer("👋 Привет! Я бот, EdHacks. Помогу тебе написать хороший текст. Давай начнем!")

@router.message(Command("clear"))
async def clear_history(message: types.Message):
    """Очищает историю сообщений пользователя"""
    user_id = message.from_user.id
    if user_id in user_messages:
        user_messages[user_id] = []
    await message.answer("🧹 История разговора очищена!")

@router.message()
async def handle_message(message: types.Message):
    """Обрабатывает входящее сообщение пользователя."""
    user_id = message.from_user.id
    user_input = message.text

    # Очищаем старые сообщения перед обработкой нового
    await cleanup_old_messages()
    
    response = await chat_with_assistant(user_id, user_input)
    await message.reply(response)

async def main():
    """Запуск бота (aiogram 3.x)"""
    dp.include_router(router)  # Подключаем router
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())  # Новый формат запуска для aiogram 3.x
