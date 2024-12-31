import json
import hashlib
import base64
import logging
import uuid

from typing import Any, Dict
from aiohttp import ClientSession

from src_bot.config.payment_config import payment_config
from src_bot.db.database import get_database
from src_bot.schemas.premium import Payment

logger = logging.getLogger(__name__)

MERCHANT_UUID = payment_config.CRYPTOMUS_MERCHANT_UUID
CRYPTOMUS_API_KEY = payment_config.CRYPTOMUS_API_KEY


def generate_headers(data: str) -> Dict[str, Any]:
    sign = hashlib.md5(base64.b64encode(data.encode("ascii")) + CRYPTOMUS_API_KEY.encode("ascii")).hexdigest()
    return {"merchant": MERCHANT_UUID, "sign": sign, "content-type": "application/json"}


async def create_invoice(client_id: int, payment: Payment) -> Any:
    idempotence_key = str(uuid.uuid4())
    async with ClientSession() as session:
        json_dumps = json.dumps({
            "amount": str(payment.amount),
            "order_id": idempotence_key,
            "currency": payment.currency,
            "network": None,
            "lifetime": 900,
            "url_callback": payment_config.URL_CALLBACK
        })

        response = await session.post(
            "https://api.cryptomus.com/v1/payment",
            data=json_dumps,
            headers=generate_headers(json_dumps)
        )
        invoice = await response.json()
        logger.warn(invoice)
        if "result" in invoice and "uuid" in invoice["result"]:
            db = get_database()
            db.add_new_payment(
                user_id=client_id,
                amount=float(invoice["result"]["amount"]),
                currency=invoice["result"]["currency"],
                payment_type="cryptomus",
                payment_id=invoice['result']['uuid'],
                order_id=invoice['result']["order_id"],
                status=invoice["result"].get("status", "pending"),
                additional_data={"uuid": invoice["result"]["uuid"], "url": invoice["result"]["url"]}
            )
            return invoice["result"]["url"]
        return str(invoice)


async def get_invoice(db, uuid: str) -> Any:
    """
    Получает информацию о счете по его UUID.

    Аргументы:
        db: Экземпляр класса Database.
        uuid (str): Уникальный идентификатор счета.

    Возвращает:
        Any: Данные о счете в формате JSON, включающие статус и детали платежа.

    Пример:
        @router.callback_query(lambda c: c.data.startswith("0_"))
        async def check_order(query: CallbackQuery) -> None:
            uuid = query.data.split("_")[1]
            invoice = await get_invoice(uuid)

            if invoice["result"]["status"] == "paid":
                await query.answer()
                await query.message.answer("Счет оплачен!")
            else:
                await query.answer("Счет не оплачен!")
    """
    async with ClientSession() as session:
        json_dumps = json.dumps({"uuid": uuid})
        response = await session.post(
            "https://api.cryptomus.com/v1/payment/info",
            data=json_dumps,
            headers=generate_headers(json_dumps)
        )
        invoice = await response.json()

        pay_doc = db.payment_collection.find_one({"additional_data.uuid": uuid})
        if pay_doc and "result" in invoice:
            new_status = invoice["result"].get("status", pay_doc["status"])
            db.update_payment_status(pay_doc["_id"], new_status)

        return invoice
