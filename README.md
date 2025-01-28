# EdHacks AI Telegram Bot

EdHacks - это Telegram бот, использующий OpenAI API для помощи в написании и улучшении текстов.

## Возможности

- 💬 Общение с AI ассистентом
- 🔄 Сохранение контекста разговора


## Установка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/your-username/edhacks-bot.git
cd edhacks-bot
```

2. Установите зависимости:
```bash
pip install -r requirements.txt
```

3. Создайте файл `.env` и добавьте необходимые переменные окружения:
```bash
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
OPENAI_API_KEY=your_openai_api_key
ASSISTANT_ID=your_assistant_id
```

## Запуск

```bash
python bot.py
```

## Команды бота

- `/start` - Начать общение с ботом
- `/clear` - Очистить историю сообщений

## Требования

- Python 3.7+
- aiogram 3.x
- openai
- python-dotenv