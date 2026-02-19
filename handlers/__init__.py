"""
Регистрация всех обработчиков бота.
main.py вызывает register_all(bot), и каждый подмодуль вешает свои хендлеры.
"""
from . import admin, callbacks, orders, start


def register_all(bot):
    """Подключает /start, кнопки, заказы, админ-команды."""
    start.register(bot)
    callbacks.register(bot)
    orders.register(bot)
    admin.register(bot)
