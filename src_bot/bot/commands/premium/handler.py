from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import CallbackContext

from src_bot.bot.enums import CallbackQueryEnum
import src_bot.bot.messages as messages


async def premium_handler(update: Update, context: CallbackContext):
    # from bot.bot import register_user_if_not_exists
    #
    # await register_user_if_not_exists(
    #     update,
    #     context,
    #     update.message.from_user,
    # )
    reply_text: str = messages.payment_message
    reply_markup: InlineKeyboardMarkup = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton('🔐 1 year | 100 msg/day | $44.99| $3.7/month',
                                  callback_data=f'{CallbackQueryEnum.PREMIUM_TARIFF}|12')],
            [InlineKeyboardButton('🔐 6 months | 100 msg/day | $24.99| $4.1/month',
                                  callback_data=f'{CallbackQueryEnum.PREMIUM_TARIFF}|6')],
            [InlineKeyboardButton('🔐 1 month | 100 msg/day | $5.99',
                                  callback_data=f'{CallbackQueryEnum.PREMIUM_TARIFF}|1')],
        ]
    )

    # Нужно два ифа, т.к мы можем вернуться сюда из коллбебка
    if update.message:
        await update.message.reply_text(
            text=reply_text,
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup,
        )
    elif update.callback_query:
        await update.callback_query.message.reply_text(
            text=reply_text,
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup,
        )
