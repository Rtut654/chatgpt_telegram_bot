from typing import Dict

from telegram import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.constants import ParseMode
from telegram.ext import CallbackContext

from src_bot.bot.enums import CallbackQueryEnum, PaymentType
from src_bot.bot import messages
from src_bot.schemas.premium import Payment, payment_by_tariff
import src_bot.services.payment.stripe.invoice as stripe
import src_bot.services.payment.yookassa.invoice as yookassa
import src_bot.services.payment.cryptomus.invoice as cryptomus


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
    prices: Dict[str, Payment] = payment_by_tariff[month_tariff]

    reply_markup: InlineKeyboardMarkup = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text=str(prices[PaymentType.stripe]),
                    callback_data=f'{CallbackQueryEnum.PAYMENT_CHOOSE}|{month_tariff}|{PaymentType.stripe}')
            ],
            [
                InlineKeyboardButton(
                    text=str(prices[PaymentType.yookassa]),
                    callback_data=f'{CallbackQueryEnum.PAYMENT_CHOOSE}|{month_tariff}|{PaymentType.yookassa}')
            ],
            [
                InlineKeyboardButton(
                    text=str(prices[PaymentType.cryptomus]),
                    callback_data=f'{CallbackQueryEnum.PAYMENT_CHOOSE}|{month_tariff}|{PaymentType.cryptomus}')
            ],
        ],
    )
    await query.edit_message_reply_markup(reply_markup=reply_markup)


async def callback_query_payment_choose(
        update: Update,
        context: CallbackContext,
):
    query: CallbackQuery = update.callback_query

    [_, month_tariff, payment_type] = query.data.split('|')
    payment = payment_by_tariff[month_tariff][payment_type]

    if payment.type == PaymentType.stripe:
        payment_link = await stripe.create_invoice(
            client_id=query.from_user.id,
            payment=payment,
        )
        # TODO - логика изменения статуса на премиум - вебхук на проверку статуса заявки
        await query.message.reply_text(
            text=messages.confirmation_payment_message,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(text='💳 Pay', url=payment_link)]]),
            parse_mode=ParseMode.HTML)
    elif payment.type == PaymentType.yookassa:
        payment_link = await yookassa.create_invoice(
            client_id=query.from_user.id,
            payment=payment,
        )
        await query.message.reply_text(
            text=messages.confirmation_payment_message,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(text='💳 Pay', url=payment_link)]]),
            parse_mode=ParseMode.HTML)
    elif payment.type == PaymentType.cryptomus:
        payment_link = await cryptomus.create_invoice(
            client_id=query.from_user.id,
            payment=payment,
        )
        # logger = logging.getLogger(__name__)
        await query.message.reply_text(
            text=messages.confirmation_payment_message,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(text='💳 Pay', url=payment_link)]]),
            parse_mode=ParseMode.HTML)
    await query.answer()
