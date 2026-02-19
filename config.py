"""
Конфигурация бота из переменных окружения.
Токен и ID админа не хранятся в коде — только в .env (или в системе).
"""
import os
from pathlib import Path

from dotenv import load_dotenv

# Загружаем .env из папки проекта (рядом с config.py)
_env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(_env_path)


def _get_required(key: str, description: str) -> str:
    """Читает обязательную переменную окружения. Выходит с понятной ошибкой, если нет."""
    value = os.environ.get(key, "").strip()
    if not value:
        print(
            f"Ошибка: не задана переменная окружения {key}.\n"
            f"  {description}\n"
            f"  Создайте файл .env (скопируйте из .env.example) и заполните значения."
        )
        raise SystemExit(1)
    return value


# Токен бота (обязательно)
TELEGRAM_BOT_TOKEN = _get_required(
    "TELEGRAM_BOT_TOKEN",
    "Токен выдаёт @BotFather в Telegram.",
)

# ID чата администратора — сюда пересылаются заказы (обязательно для пересылки)
_admin_id_raw = _get_required(
    "ADMIN_CHAT_ID",
    "Узнать ID: напишите боту @userinfobot в Telegram, скопируйте 'Id'.",
)
ADMIN_CHAT_ID = int(_admin_id_raw.strip().replace("\r", "").replace("\n", ""))

# Несколько админов: в .env можно задать ADMIN_CHAT_IDS=id1,id2 — тогда заказы уйдут всем
_admin_ids_raw = os.environ.get("ADMIN_CHAT_IDS", "").strip()
if _admin_ids_raw:
    ADMIN_CHAT_IDS = [
        int(x.strip()) for x in _admin_ids_raw.split(",") if x.strip()
    ]
else:
    ADMIN_CHAT_IDS = [ADMIN_CHAT_ID]

# Папка для логов и БД
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = Path(os.environ.get("DATA_DIR", str(BASE_DIR / "data")))
ORDERS_LOG_FILE = DATA_DIR / "orders.log"
ORDERS_DB_FILE = DATA_DIR / "orders.db"
BOT_LOG_FILE = DATA_DIR / "bot.log"
