import json
import hashlib
import base64

from typing import Any, Dict
from aiohttp import  ClientSession
from config import MERCHANT_UUID, CRYPTOMUS_API_KEY

def generate_headers(data: str) -> Dict[str, Any]:
    sign = hashlib.md5(base64.b64encode (data. encode ("ascii")) + CRYPTOMUS_API_KEY.encode("ascii")).hexdigest()
    return {"merchant": MERCHANT_UUID, "sign": sign, "content-type": "application/json"}

async def create_invoice(user_id: int, amount: int, currency: str, network: str) -> Any:
    """
       Создает счет на оплату с помощью API Cryptomus.

       Аргументы:
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
            "lifetime": 900
        })

        response = await session.post(
            "https://api.cryptomus.com/v1/payment",
            data=json_dumps,
            headers=generate_headers(json_dumps)
        )

        return await response.json()


async def get_invoice(uuid: str) -> Any:
    """
    Получает информацию о счете по его UUID.

    Аргументы:
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
        return await response.json()