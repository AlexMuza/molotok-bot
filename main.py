"""
Точка входа: загрузка конфига, настройка логов, создание бота, регистрация обработчиков, запуск polling.
Запуск: из корня проекта выполнить  python main.py
"""
import logging
import sys

import config  # сразу загружает .env и проверяет TELEGRAM_BOT_TOKEN, ADMIN_CHAT_ID

from bot import bot
from handlers import register_all

# Логирование в файл и в консоль
config.DATA_DIR.mkdir(parents=True, exist_ok=True)
_file_handler = logging.FileHandler(config.BOT_LOG_FILE, encoding="utf-8")
_file_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
_console = logging.StreamHandler(sys.stdout)
_console.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
logging.getLogger().setLevel(logging.INFO)
logging.getLogger().addHandler(_file_handler)
logging.getLogger().addHandler(_console)

if __name__ == "__main__":
    register_all(bot)
    logging.info("Бот «Молоток» запущен.")
    print("Бот «Молоток» запущен. Остановка: Ctrl+C")
    try:
        bot.infinity_polling()
    except KeyboardInterrupt:
        print("Остановлено пользователем.")
    except Exception as e:
        logging.exception("Ошибка: %s", e)
        raise
