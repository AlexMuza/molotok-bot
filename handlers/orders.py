"""
Обработка текстовых сообщений как заказов:
1) rate limit — не чаще раз в 60 сек от одного пользователя;
2) сохраняем заказ в файл и в БД;
3) отправляем подтверждение пользователю;
4) пересылаем заказ всем администраторам.
"""
import time
import logging

import config
from storage.orders import save_order

logger = logging.getLogger(__name__)

# Ограничение: один заказ от одного user_id не чаще чем раз в ORDER_COOLDOWN_SEC секунд
ORDER_COOLDOWN_SEC = 60
_last_order_time: dict[int, float] = {}


def register(bot):
    @bot.message_handler(content_types=["text"])
    def handle_text(message):
        if message.text.startswith("/"):
            return  # команды не считаем заказом

        user_id = message.from_user.id if message.from_user else 0
        username = message.from_user.username if message.from_user else None
        chat_id = message.chat.id
        order_text = message.text

        # Rate limit
        now = time.time()
        if user_id in _last_order_time:
            elapsed = now - _last_order_time[user_id]
            if elapsed < ORDER_COOLDOWN_SEC:
                bot.send_message(
                    message.chat.id,
                    "⏳ Подождите минуту перед следующим заказом.",
                    parse_mode="html",
                )
                return
        _last_order_time[user_id] = now

        # 1) Логирование: файл + SQLite (получаем id заказа для админа и /done)
        order_id = save_order(order_text, user_id=user_id, username=username, chat_id=chat_id)

        # 2) Подтверждение клиенту
        order_response = f"""
✅ <b>Заказ принят!</b>

Мы получили ваш запрос:
"{order_text}"

Менеджер свяжется с вами в ближайшее время.

📞 Для срочных вопросов: +7 958 509-44-99
        """
        bot.send_message(message.chat.id, order_response, parse_mode="html")

        # 3) Пересылка всем администраторам (с номером заказа для /done)
        admin_text = (
            f"📦 <b>Новый заказ №{order_id}</b>\n\n"
            f"👤 user_id: <code>{user_id}</code>\n"
            f"📛 username: @{username or '—'}\n"
            f"💬 Чат: <code>{chat_id}</code>\n\n"
            f"Текст заказа:\n{order_text}\n\n"
            f"Чтобы уведомить клиента: /done {order_id}"
        )
        for admin_id in config.ADMIN_CHAT_IDS:
            try:
                bot.send_message(admin_id, admin_text, parse_mode="html")
            except Exception as e:
                logger.exception("Не удалось отправить заказ админу %s: %s", admin_id, e)
