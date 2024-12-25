from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import CallbackContext

from src_bot.bot.enums import CallbackQueryEnum


async def premium_handler(update: Update, context: CallbackContext):
    # from bot.bot import register_user_if_not_exists
    #
    # await register_user_if_not_exists(
    #     update,
    #     context,
    #     update.message.from_user,
    # )
    # TODO: replace text
    reply_text: str = 'reply_text'

    reply_markup: InlineKeyboardMarkup = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text='1 month',
                    callback_data=f'{CallbackQueryEnum.PREMIUM_MONTH}|1',
                ),
            ],
            [
                InlineKeyboardButton(
                    text='3 month',
                    callback_data=f'{CallbackQueryEnum.PREMIUM_MONTH}|3',
                ),
            ],
            [
                InlineKeyboardButton(
                    text='6 month',
                    callback_data=f'{CallbackQueryEnum.PREMIUM_MONTH}|6',
                ),
            ],
        ],
    )

    await update.message.reply_text(
        text=reply_text,
        parse_mode=ParseMode.HTML,
        reply_markup=reply_markup,
    )
