"""
Команды только для администраторов: /stats, /broadcast, /done.
"""
import logging
import time

import config
from storage.orders import get_stats, get_chat_id_by_order_id, get_all_chat_ids

logger = logging.getLogger(__name__)


def _is_admin(user_id: int) -> bool:
    return user_id in config.ADMIN_CHAT_IDS


def register(bot):
    @bot.message_handler(commands=["stats"])
    def cmd_stats(message):
        if not _is_admin(message.from_user.id if message.from_user else 0):
            return
        today, week = get_stats(7)
        text = (
            "📊 <b>Статистика заказов</b>\n\n"
            f"Сегодня: <b>{today}</b>\n"
            f"За 7 дней: <b>{week}</b>"
        )
        bot.send_message(message.chat.id, text, parse_mode="html")

    @bot.message_handler(commands=["broadcast"])
    def cmd_broadcast(message):
        if not _is_admin(message.from_user.id if message.from_user else 0):
            return
        parts = message.text.split(maxsplit=1)
        if len(parts) < 2:
            bot.send_message(
                message.chat.id,
                "Использование: /broadcast <текст сообщения>",
                parse_mode="html",
            )
            return
        text = parts[1].strip()
        chat_ids = get_all_chat_ids()
        if not chat_ids:
            bot.send_message(message.chat.id, "Нет ни одного чата для рассылки.")
            return
        sent, failed = 0, 0
        for cid in chat_ids:
            try:
                bot.send_message(cid, text, parse_mode="html")
                sent += 1
                time.sleep(0.05)  # защита от flood
            except Exception as e:
                failed += 1
                logger.warning("broadcast to %s failed: %s", cid, e)
        bot.send_message(
            message.chat.id,
            f"✅ Рассылка: отправлено {sent}, ошибок {failed}.",
            parse_mode="html",
        )

    @bot.message_handler(commands=["done"])
    def cmd_done(message):
        if not _is_admin(message.from_user.id if message.from_user else 0):
            return
        parts = message.text.split()
        if len(parts) < 2:
            bot.send_message(
                message.chat.id,
                "Использование: /done <номер_заказа>\nНапример: /done 5",
                parse_mode="html",
            )
            return
        try:
            order_id = int(parts[1])
        except ValueError:
            bot.send_message(message.chat.id, "Номер заказа должен быть числом.")
            return
        chat_id = get_chat_id_by_order_id(order_id)
        if chat_id is None:
            bot.send_message(message.chat.id, f"Заказ №{order_id} не найден.")
            return
        notice = (
            "✅ <b>Ваш заказ №%s принят в работу.</b>\n\n"
            "Менеджер свяжется с вами в ближайшее время.\n"
            "Для срочных вопросов: +7 958 509-44-99"
        ) % order_id
        try:
            bot.send_message(chat_id, notice, parse_mode="html")
            bot.send_message(
                message.chat.id,
                f"Клиенту (заказ №{order_id}) отправлено уведомление.",
                parse_mode="html",
            )
        except Exception as e:
            logger.exception("done: send to chat_id %s failed: %s", chat_id, e)
            bot.send_message(message.chat.id, f"Не удалось отправить: {e}")
