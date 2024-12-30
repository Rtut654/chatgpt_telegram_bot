import json
import logging
import asyncio
import uuid

import yookassa

from src_bot.schemas.premium import Payment
from src_bot.config.payment_config import payment_config

from bot.database import get_database

yookassa.Configuration.account_id = payment_config.YOOKASSA_CLIENT_ID
yookassa.Configuration.secret_key = payment_config.YOOKASSA_SECRET_KEY

logger = logging.getLogger(__name__)


# return_tg_url = config.return_tg_url
# wh_Url = config.wh_Url

# Webhook.add({
#     "event": "payment.succeeded",
#     "url": wh_Url,
# })
#
# Webhook.add({
#     "event": "payment.waiting_for_capture",
#     "url": wh_Url,
# })
#
# Webhook.add({
#     "event": "payment.canceled",
#     "url": wh_Url,
# })

# list = Webhook.list() проверка


async def create_invoice(client_id: int, payment: Payment):
    """
        Examples:
            payment_data = payment(price, f'Покупка курса по мыловарению "{title}", пользователь - {username}.')
            link_for_pay = payment_data['confirmation']['confirmation_url']
            payment_id = payment_data['id']

        Raises:
            ValueError: Если цена меньше или равна нулю или описание пустое.
        """

    # price = payment.amount
    idempotence_key = str(uuid.uuid4())
    try:
        p = yookassa.Payment.create({
            "amount": {
                "value": payment.amount,
                "currency": "RUB"
            },
            "confirmation": {
                "type": "redirect",
                "return_url": payment_config.URL_CALLBACK
            },
            "capture": True,
            "description": payment.desc
        }, idempotence_key)

        payment_data = json.loads(p.json())
        db = get_database()
        db.add_new_payment(
            user_id=client_id,
            amount=float(payment_data["amount"]["value"]),
            currency=payment_data["amount"]["currency"],
            payment_type="yookassa",
            payment_id=payment_data["id"],
            order_id=None,
            status=payment_data["status"],
            additional_data={"description": payment_data["description"]}
        )
        return p.confirmation.confirmation_url
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        raise
