import json
import hashlib
import base64
import logging

from flask import Response

from src_bot.config.payment_config import payment_config

logger = logging.getLogger(__name__)

MERCHANT_UUID = payment_config.CRYPTOMUS_MERCHANT_UUID
CRYPTOMUS_API_KEY = payment_config.CRYPTOMUS_API_KEY


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
        return Response(status=405)  # Метод не разрешен

    raw_data = request.body.decode("utf-8")

    # Парсим JSON в словарь
    try:
        data = json.loads(raw_data)
    except ValueError:
        return Response(status=400)

    # Извлекаем sign
    if 'sign' not in data:
        return Response(status=400)

    sign = data['sign']
    del data['sign']

    # Подготовка данных для проверки подписи
    json_str = json.dumps(data, ensure_ascii=False)
    json_str = json_str.replace('/', '\\/')
    json_base64 = base64.b64encode(json_str.encode('utf-8')).decode('utf-8')
    to_hash = json_base64 + CRYPTOMUS_API_KEY
    hash_check = hashlib.md5(to_hash.encode('utf-8')).hexdigest()

    if hash_check != sign:
        return Response(status=403)

    # Если подпись корректна, обрабатываем данные
    payment_status = data.get("status", "")
    payment_id = data.get("uuid")

    pay_doc = db.payment_collection.find_one({"payment_id": payment_id})
    if not pay_doc:
        logger.error(f"Платеж с ID {payment_id} не найден в базе данных.")
        return Response(status=400)

    if not payment_id:
        logger.error("Не указан payment_id (uuid) в данных платежа.")
        return Response(status=400)

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

    return Response(status=200)
