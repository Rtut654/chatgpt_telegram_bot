import json
import hashlib
import base64
import logging

from django.http import HttpResponse
from datetime import datetime, timedelta
from typing import Any, Dict
from aiohttp import  ClientSession

from config import MERCHANT_UUID, CRYPTOMUS_API_KEY, url_callback

logger = logging.getLogger(__name__)


def generate_headers(data: str) -> Dict[str, Any]:
    sign = hashlib.md5(base64.b64encode (data. encode ("ascii")) + CRYPTOMUS_API_KEY.encode("ascii")).hexdigest()
    return {"merchant": MERCHANT_UUID, "sign": sign, "content-type": "application/json"}

async def create_invoice(db, user_id: int, amount: int, currency: str, network: str) -> Any:
    """
       Создает счет на оплату с помощью API Cryptomus.

       Аргументы:
           db: Экземпляр класса Database.
           user_id (int): Идентификатор пользователя.
           amount (int): Сумма платежа.
           currency (str): Валюта платежа (например, "USDT").
           network (str): Сеть для платежа (например, "TRC20").

       Возвращает:
           Any: Ответ API в формате JSON.

       Пример:
       async def start(message: Message) -> None:
            invoice = await create_invoice(message.from_user.id, amount=100, currency="USDT", network="TRC20")

            check_button = InlineKeyboardButton(
                text="Проверить",
                callback_data=f"o_{invoice['result']['uuid']}"
            )

            markup = InlineKeyboardMarkup(inline_keyboard=[[check_button]])

            await message.reply(
                f"Ваш счет: {invoice['result']['url']}",
                reply_markup=markup
            )
       """
    async with ClientSession() as session:
        json_dumps = json.dumps({
            "amount": amount,
            "order_id": f"TEST-ORDER-{user_id}-000",
            "currency": currency,
            "network": network,
            "lifetime": 900,
            "url_callback": url_callback #	Url to which webhooks with payment status will be sent
        })

        response = await session.post(
            "https://api.cryptomus.com/v1/payment",
            data=json_dumps,
            headers=generate_headers(json_dumps)
        )
        invoice = await response.json()

        if "result" in invoice and "uuid" in invoice["result"]:
            db.add_new_payment(
                user_id=user_id,
                amount=float(invoice["result"]["amount"]),
                currency=invoice["result"]["currency"],
                payment_type="cryptomus",
                payment_id=invoice['result']['uuid'],
                order_id=None,
                status=invoice["result"].get("status", "pending"),
                additional_data={"uuid": invoice["result"]["uuid"], "url": invoice["result"]["url"]}
            )
        return invoice


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


def cryptomus_webhook_handler(db, request):
    """
        Обработчик вебхука от Cryptomus.

        Эта функция принимает POST-запрос от платежной системы Cryptomus, проверяет подпись, полученную в теле запроса, и на
        основании данных о статусе платежа обновляет статус в базе данных. Если статус платежа — "paid", дополнительно
        активируется подписка для пользователя, связанного с платежом.

        Args:
            request (HttpRequest): Django HttpRequest, ожидается POST-запрос с JSON-данными вебхука.
            db

        Returns:
            HttpResponse: Возвращает HTTP 200 при успешной обработке, либо ошибочный статус при возникновении проблем.
    """

    if request.method != "POST":
        return HttpResponse(status=405)  # Метод не разрешен

    raw_data = request.body.decode("utf-8")

    # Парсим JSON в словарь
    try:
        data = json.loads(raw_data)
    except ValueError:
        return HttpResponse(status=400)

    # Извлекаем sign
    if 'sign' not in data:
        return HttpResponse(status=400)

    sign = data['sign']
    del data['sign']

    # Подготовка данных для проверки подписи
    json_str = json.dumps(data, ensure_ascii=False)
    json_str = json_str.replace('/', '\\/')
    json_base64 = base64.b64encode(json_str.encode('utf-8')).decode('utf-8')
    to_hash = json_base64 + CRYPTOMUS_API_KEY
    hash_check = hashlib.md5(to_hash.encode('utf-8')).hexdigest()

    if hash_check != sign:
        return HttpResponse(status=403)

    # Если подпись корректна, обрабатываем данные
    payment_status = data.get("status", "")
    payment_id = data.get("uuid")

    pay_doc = db.payment_collection.find_one({"payment_id": payment_id})
    if not pay_doc:
        logger.error(f"Платеж с ID {payment_id} не найден в базе данных.")
        return HttpResponse(status=400)

    if not payment_id:
        logger.error("Не указан payment_id (uuid) в данных платежа.")
        return HttpResponse(status=400)

    db.update_payment_status(pay_doc["_id"], payment_status)
    logger.info(f"Статус платежа {payment_id} обновлен на {payment_status}.")

    if payment_status == "paid":
        # Активируем подписку пользователю на основании telegram_id
        telegram_id = pay_doc.get("telegram_id")
        if telegram_id:
            db.update_user_subscription(telegram_id, duration_days=30)
            logger.info(f"Подписка для пользователя с telegram_id={telegram_id} активирована на 30 дней.")
        else:
            logger.warning(f"Для платежа {payment_id} не указан telegram_id, невозможно активировать подписку.")

    return HttpResponse(status=200)
