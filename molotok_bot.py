# -*- coding: utf-8 -*-
import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

print(" Инициализация бота МОЛОТОК...")

class MolotokBot:
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /start"""
        user = update.effective_user
        print(f" Пользователь {user.first_name} запустил бота")
        
        keyboard = [
            [InlineKeyboardButton(" Каталог товаров", callback_data='catalog')],
            [InlineKeyboardButton(" Акции и скидки", callback_data='promotions')],
            [InlineKeyboardButton(" Контакты", callback_data='contacts')],
            [InlineKeyboardButton(" Сделать заказ", callback_data='order')],
            [InlineKeyboardButton(" Доставка", callback_data='delivery')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        welcome_text = f"""
 Приветствуем в магазине "МОЛОТОК", {user.first_name}!

 Строительные материалы  Инструменты  Крепеж

 Супер-сервис  Низкие цены  Уникальный ассортимент

Выберите опцию ниже
        """
        
        await update.message.reply_text(welcome_text, reply_markup=reply_markup)

    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик нажатий кнопок"""
        query = update.callback_query
        await query.answer()
        
        print(f" Нажата кнопка: {query.data}")
        
        if query.data == 'catalog':
            await self.show_catalog(query)
        elif query.data == 'promotions':
            await self.show_promotions(query)
        elif query.data == 'contacts':
            await self.show_contacts(query)
        elif query.data == 'order':
            await self.start_order(query)
        elif query.data == 'delivery':
            await self.show_delivery(query)
        elif query.data == 'back':
            await self.back_to_main(query)

    async def back_to_main(self, query):
        """Возврат в главное меню"""
        keyboard = [
            [InlineKeyboardButton(" Каталог товаров", callback_data='catalog')],
            [InlineKeyboardButton(" Акции и скидки", callback_data='promotions')],
            [InlineKeyboardButton(" Контакты", callback_data='contacts')],
            [InlineKeyboardButton(" Сделать заказ", callback_data='order')],
            [InlineKeyboardButton(" Доставка", callback_data='delivery')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(" Главное меню магазина 'МОЛОТОК'\n\nВыберите опцию:", reply_markup=reply_markup)

    async def show_catalog(self, query):
        """Показываем каталог товаров"""
        catalog_text = """
 КАТАЛОГ ТОВАРОВ:

 КРАСКИ И ЛАКИ:
 Краска акриловая белая 5л - 2500
 Эмаль по металлу 2.5л - 1800  
 Грунтовка универсальная 10л - 3200

 КРЕПЕЖ И ГВОЗДИ:
 Гвозди строительные 100мм (1кг) - 150
 Саморезы по дереву 4.5x75 (100шт) - 220
 Дюбель-гвоздь 8x80 (50шт) - 180

 ЗАМКИ И ФУРНИТУРА:
 Замок накладной - 850
 Цилиндровый механизм - 450
 Ручка дверная - 1200
        """
        
        keyboard = [
            [InlineKeyboardButton(" Сделать заказ", callback_data='order')],
            [InlineKeyboardButton(" Акции", callback_data='promotions')],
            [InlineKeyboardButton(" Назад", callback_data='back')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(catalog_text, reply_markup=reply_markup)

    async def show_promotions(self, query):
        """Показываем акции"""
        promotions_text = """
 АКТУАЛЬНЫЕ АКЦИИ:

 СЕЗОННАЯ РАСПРОДАЖА:
 Краска акриловая - скидка 15%
 Все инструменты - скидка 10%

 БЕСПЛАТНАЯ ДОСТАВКА:
 При заказе от 5000 в пределах Воронежа
        """
        
        keyboard = [
            [InlineKeyboardButton(" Каталог", callback_data='catalog')],
            [InlineKeyboardButton(" Заказать", callback_data='order')],
            [InlineKeyboardButton(" Назад", callback_data='back')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(promotions_text, reply_markup=reply_markup)

    async def show_contacts(self, query):
        """Показываем контакты"""
        contacts_text = """
 МАГАЗИН "МОЛОТОК"

 АДРЕС:
Воронеж, [Ваш адрес]

 РЕЖИМ РАБОТЫ:
Пн-Пт: 8:00 - 20:00
Сб-Вс: 9:00 - 18:00

 ТЕЛЕФОН:
+7 (900) 000-00-00
        """
        
        keyboard = [
            [InlineKeyboardButton(" Сделать заказ", callback_data='order')],
            [InlineKeyboardButton(" Открыть карту", url='https://yandex.ru/maps')],
            [InlineKeyboardButton(" Назад", callback_data='back')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(contacts_text, reply_markup=reply_markup)

    async def start_order(self, query):
        """Начинаем заказ"""
        order_text = """
 ОФОРМЛЕНИЕ ЗАКАЗА

Для заказа напишите нам:
 Список нужных товаров
 Количество
 Ваш номер телефона

 Или позвоните:
+7 (900) 000-00-00
        """
        
        keyboard = [
            [InlineKeyboardButton(" Каталог", callback_data='catalog')],
            [InlineKeyboardButton(" Контакты", callback_data='contacts')],
            [InlineKeyboardButton(" Назад", callback_data='back')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(order_text, reply_markup=reply_markup)

    async def show_delivery(self, query):
        """Информация о доставке"""
        delivery_text = """
 УСЛОВИЯ ДОСТАВКИ:

 КУРЬЕРСКАЯ ДОСТАВКА:
 По Воронежу - 300
 Бесплатно от 5000

 САМОВЫВОЗ:
 Бесплатно
 Готовность: 30 минут
        """
        
        keyboard = [
            [InlineKeyboardButton(" Сделать заказ", callback_data='order')],
            [InlineKeyboardButton(" Назад", callback_data='back')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(delivery_text, reply_markup=reply_markup)

def main():
    """Запуск бота"""
    # Получаем токен из переменных окружения Railway
    BOT_TOKEN = os.environ.get('BOT_TOKEN')
    
    if not BOT_TOKEN:
        print(" ОШИБКА: Переменная окружения BOT_TOKEN не установлена!")
        print(" Установите переменную BOT_TOKEN в настройках Railway")
        return
    
    try:
        print(" Запуск бота МОЛОТОК на Railway...")
        application = Application.builder().token(BOT_TOKEN).build()
        
        bot = MolotokBot()
        
        application.add_handler(CommandHandler("start", bot.start))
        application.add_handler(CallbackQueryHandler(bot.button_handler))
        
        print(" Бот успешно инициализирован!")
        print(" Бот 'Молоток' запущен и работает 24/7!")
        print(" Хостинг: Railway.app")
        application.run_polling()
        
    except Exception as e:
        print(f" Ошибка: {e}")

if __name__ == '__main__':
    main()
