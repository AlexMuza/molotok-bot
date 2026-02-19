"""
Команда /start: приветствие с именем и кнопки (Каталог, Заказ, Контакты, FAQ, Акции).
"""
from telebot import types


def register(bot):
    @bot.message_handler(commands=["start"])
    def send_welcome(message):
        name = "гость"
        if message.from_user:
            name = message.from_user.first_name or message.from_user.username or name
        name = name or "гость"

        markup = types.InlineKeyboardMarkup(row_width=2)
        btn_catalog = types.InlineKeyboardButton("🛍️ Каталог", callback_data="catalog")
        btn_order = types.InlineKeyboardButton("📦 Заказ", callback_data="order")
        btn_contacts = types.InlineKeyboardButton("📞 Контакты", callback_data="contacts")
        btn_faq = types.InlineKeyboardButton("❓ Частые вопросы", callback_data="faq")
        btn_promo = types.InlineKeyboardButton("🏷️ Акции", callback_data="promo")
        markup.add(btn_catalog, btn_order, btn_contacts, btn_faq, btn_promo)

        welcome_text = f"""
<b>Добро пожаловать в магазин «Молоток», {name}!</b>

Выберите нужный раздел:
        """
        bot.send_message(
            message.chat.id, welcome_text, parse_mode="html", reply_markup=markup
        )
