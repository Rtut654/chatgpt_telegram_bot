import json
import logging

import yookassa
from yookassa.domain.notification import WebhookNotificationEventType, WebhookNotification
from flask import Response

logger = logging.getLogger(__name__)


def yookassa_webhook_handler(request, db):
    """
        Обработчик вебхуков от YooKassa.

        Эта функция принимает POST-запросы от сервиса YooKassa, обрабатывает уведомления о событиях платежей,
        проверяет их корректность и обновляет статус платежа в базе данных. В случае успешного завершения платежа
        активирует подписку для соответствующего пользователя на указанный период.

        Args:
            request (HttpRequest)
            db:
        Returns:
            HttpResponse
        """
    try:
        event_json = json.loads(request.body)
    except json.JSONDecodeError:
        logger.error("Не удалось декодировать JSON из тела запроса вебхука.")
        raise

    try:
        # Создание объекта уведомления
        notification_object = WebhookNotification(event_json)
        response_object = notification_object.object
        payment_id = response_object.id
        payment_status = response_object.status

        # В зависимости от типа события можно задать логику
        if notification_object.event == WebhookNotificationEventType.PAYMENT_SUCCEEDED:
            # Платеж успешно оплачен
            new_status = "paid"
        elif notification_object.event == WebhookNotificationEventType.PAYMENT_WAITING_FOR_CAPTURE:
            # Платеж ждёт подтверждения
            new_status = "waiting_for_capture"
        elif notification_object.event == WebhookNotificationEventType.PAYMENT_CANCELED:
            # Платеж отменён
            new_status = "canceled"
        else:
            # Если событие неизвестно или нас не интересует — сообщаем об ошибке
            logger.warning(f"Неизвестный тип события вебхука: {notification_object.event}")
            return Response(status=400)

        pay_doc = db.payment_collection.find_one({"payment_id": payment_id})
        if not pay_doc:
            logger.error(f"Платеж с ID {payment_id} не найден в базе данных.")
            return Response(status=400)

        # Обновляем статус платежа в базе данных
        db.update_payment_status(pay_doc["_id"], new_status)
        logger.info(f"Статус платежа {payment_id} обновлен на {new_status}.")
        # Активируем подписку пользователю на основании telegram_id
        telegram_id = pay_doc.get("telegram_id")
        if telegram_id:
            db.update_user_subscription(telegram_id, duration_days=30)
            logger.info(f"Подписка для пользователя с telegram_id={telegram_id} активирована на 30 дней.")
        else:
            logger.warning(f"Для платежа {payment_id} не указан telegram_id, невозможно активировать подписку.")

        return Response(status=200)

    except Exception as e:
        logger.error(f"Ошибка при обработке уведомления вебхука: {str(e)}")
        return Response(status=400)
