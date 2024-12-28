from telegram.ext import Application, CallbackQueryHandler, CommandHandler
from telegram.ext.filters import BaseFilter

from src_bot.bot.commands.premium.callback import (
    callback_query_premium_month_handle,
    callback_query_payment_choose,
)
from src_bot.bot.commands.premium.handler import premium_handler
from src_bot.bot.enums import CallbackQueryEnum, CommandEnum


def add_handlers(
    application: Application,
    filters: BaseFilter = None,
) -> None:
    application.add_handlers(
        handlers=[
            CommandHandler(
                command=CommandEnum.PREMIUM.command,
                callback=premium_handler,
                filters=filters,
            ),
            CallbackQueryHandler(
                callback=premium_handler,
                pattern=f'^{CallbackQueryEnum.PREMIUM_VIEW}',
            ),
            CallbackQueryHandler(
                callback=callback_query_premium_month_handle,
                pattern=f'^{CallbackQueryEnum.PREMIUM_TARIFF}',
            ),
            CallbackQueryHandler(
                callback=callback_query_payment_choose,
                pattern=f'^{CallbackQueryEnum.PAYMENT_CHOOSE}',
            ),
        ],
    )
