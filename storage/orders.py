"""
Логирование заказов: запись в текстовый файл (удобно смотреть) и в SQLite (удобно искать/анализировать).
"""
import sqlite3
from datetime import datetime
from pathlib import Path

# Импортируем пути из конфига после его инициализации
import config


def _ensure_data_dir():
    """Создаёт папку data, если её нет."""
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)


def _log_to_file(order_text: str, user_id: int, username: str | None, chat_id: int):
    """Добавляет одну строку в orders.log: дата, user_id, username, текст заказа."""
    _ensure_data_dir()
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    username = username or ""
    # Одна строка на заказ, поля через табуляцию (удобно открыть в Excel)
    line = f"{ts}\t{user_id}\t{chat_id}\t{username}\t{order_text}\n"
    with open(config.ORDERS_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line)


def _log_to_db(order_text: str, user_id: int, username: str | None, chat_id: int) -> int:
    """Сохраняет заказ в SQLite; возвращает id созданного заказа."""
    _ensure_data_dir()
    conn = sqlite3.connect(config.ORDERS_DB_FILE)
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                chat_id INTEGER NOT NULL,
                username TEXT,
                order_text TEXT NOT NULL
            )
            """
        )
        cur = conn.execute(
            """
            INSERT INTO orders (created_at, user_id, chat_id, username, order_text)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                datetime.now().isoformat(),
                user_id,
                chat_id,
                username or "",
                order_text,
            ),
        )
        conn.commit()
        return cur.lastrowid or 0
    finally:
        conn.close()


def save_order(order_text: str, user_id: int, username: str | None, chat_id: int) -> int:
    """
    Сохраняет заказ и в файл orders.log, и в БД orders.db.
    Возвращает id заказа в БД (для уведомления админа и /done).
    """
    _log_to_file(order_text, user_id, username, chat_id)
    return _log_to_db(order_text, user_id, username, chat_id)


def get_stats(days: int = 7) -> tuple[int, int]:
    """Возвращает (заказов за сегодня, заказов за последние days дней)."""
    import sqlite3
    from datetime import datetime, timedelta

    if not config.ORDERS_DB_FILE.exists():
        return 0, 0
    conn = sqlite3.connect(config.ORDERS_DB_FILE)
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        since = (datetime.now() - timedelta(days=days)).isoformat()
        cur = conn.execute(
            "SELECT COUNT(*) FROM orders WHERE date(created_at) = date(?)",
            (today,),
        )
        today_count = cur.fetchone()[0]
        cur = conn.execute(
            "SELECT COUNT(*) FROM orders WHERE created_at >= ?",
            (since,),
        )
        period_count = cur.fetchone()[0]
        return today_count, period_count
    finally:
        conn.close()


def get_chat_id_by_order_id(order_id: int) -> int | None:
    """Возвращает chat_id клиента по id заказа, или None."""
    import sqlite3

    if not config.ORDERS_DB_FILE.exists():
        return None
    conn = sqlite3.connect(config.ORDERS_DB_FILE)
    try:
        cur = conn.execute("SELECT chat_id FROM orders WHERE id = ?", (order_id,))
        row = cur.fetchone()
        return row[0] if row else None
    finally:
        conn.close()


def get_all_chat_ids() -> list[int]:
    """Возвращает список уникальных chat_id, которые когда-либо делали заказ (для рассылки)."""
    import sqlite3

    if not config.ORDERS_DB_FILE.exists():
        return []
    conn = sqlite3.connect(config.ORDERS_DB_FILE)
    try:
        cur = conn.execute("SELECT DISTINCT chat_id FROM orders")
        return [row[0] for row in cur.fetchall()]
    finally:
        conn.close()
