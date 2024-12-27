from typing import Dict

from telegram import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.constants import ParseMode
from telegram.ext import CallbackContext

from src_bot.bot.enums import CallbackQueryEnum
from src_bot.bot import messages

# TODO: store in MongoDB or .env
prices_by_month: Dict[str, Dict[str, str]] = {
    '1': {
        'yookassa': '100',
        'cryptomus': '100',
    },
    '6': {
        'yookassa': '100',
        'cryptomus': '100',
    },
    '12': {
        'yookassa': '100',
        'cryptomus': '100',
    },
}


async def callback_query_premium_month_handle(
        update: Update,
        context: CallbackContext,
):
    # from bot.bot import register_user_if_not_exists
    #
    # await register_user_if_not_exists(
    #     update.callback_query,
    #     context,
    #     update.callback_query.from_user
    # )

    query: CallbackQuery = update.callback_query
    [_, month_tariff] = query.data.split('|')

    month_tariff = str(month_tariff)
    prices: Dict[str, str] = prices_by_month[month_tariff]
    reply_text: str = messages.subscribe_desc_by_tariff[month_tariff]

    reply_markup: InlineKeyboardMarkup = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f'Yookassa - {prices["yookassa"]} RUB',
                    callback_data='Yookassa',
                ),
            ],
            [
                InlineKeyboardButton(
                    text=f'Cryptomus - {prices["cryptomus"]} USDT',
                    callback_data='Cryptomus',
                ),
            ],
            [
                InlineKeyboardButton(
                    text='<<',
                    callback_data=f'{CallbackQueryEnum.PREMIUM_VIEW}',
                ),
            ],
        ],
    )

    await query.answer()
    await update.callback_query.message.reply_text(
        text=reply_text,
        parse_mode=ParseMode.HTML,
        reply_markup=reply_markup,
    )
