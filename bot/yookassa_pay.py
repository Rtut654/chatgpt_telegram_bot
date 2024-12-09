import config
import json
import logging
import asyncio

from yookassa import Configuration, Webhook, Payment
from yookassa.domain.notification import WebhookNotificationEventType, WebhookNotification
from django.http import HttpResponse

Configuration.account_id = config.account_id
Configuration.secret_key = config.secret_key
return_tg_url = config.return_tg_url
wh_Url =  config.wh_Url

response = Webhook.add({
    "event": "payment.succeeded",
    "url": wh_Url,
})

response = Webhook.add({
    "event": "payment.waiting_for_capture",
    "url": wh_Url,
})

response = Webhook.add({
    "event": "payment.canceled",
    "url": wh_Url,
})

# list = Webhook.list() проверка

logger = logging.getLogger(__name__)

def payment(db, user_id: int, price: int, description: str):
    """
        Cоздание платежа с помощью Yookassa.

        Args:
            db: Экземпляр класса Database.
            user_id (int): Идентификатор пользователя.
            price (int): сумма, подлежащая оплате, в указанной валюте.
            description (str): описание платежа

        Returns:
            dict: Словарь, содержащий платежные реквизиты, возвращаемые Yookassa.

        Examples:
            payment_data = payment(price, f'Покупка курса по мыловарению "{title}", пользователь - {username}.')
            link_for_pay = payment_data['confirmation']['confirmation_url']
            payment_id = payment_data['id']

        Raises:
            ValueError: Если цена меньше или равна нулю или описание пустое.
        """


    if price <= 0:
        raise ValueError("Price must be greater than zero.")
    if not description:
        raise ValueError("Description cannot be empty.")

    try:
        p = Payment.create({
            "amount": {
                "value": str(price) + '.00',
                "currency": "RUB"
            },
            "confirmation": {
                "type": "redirect",
                "return_url": return_tg_url
            },
            "capture": True,
            "description": description
        })

        payment_data = json.loads(p.json())

        db.add_new_payment(
            user_id=user_id,
            amount=float(payment_data["amount"]["value"]),
            currency=payment_data["amount"]["currency"],
            payment_type="yookassa",
            payment_id=payment_data["id"],
            order_id=None,
            status=payment_data["status"],
            additional_data={"description": payment_data["description"]}
        )

        return json.loads(payment.json())
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        raise

async def check_payment(db,  payment_id: str):
        """
        Проверяет статус платежа и уведомляет пользователя о результате.

        Args:
            db: Экземпляр класса Database.
            payment_id (str): Идентификатор платежа для проверки.
        Raises:
            Exception: Если возникает ошибка при проверке платежа.
        """
        try:
            payment = json.loads((Payment.find_one(payment_id)).json())
            n = 0

            # Проверяем статус платежа, пока он в ожидании
            while payment['status'] == 'pending':
                logging.info(f"Проверяем платеж: {payment['description']}")
                payment = json.loads((Payment.find_one(payment_id)).json())

                # Устанавливаем время ожидания
                if n < 1:
                    wait_time = 70
                elif 0 < n <= 20:
                    wait_time = 15
                else:
                    wait_time = 60

                await asyncio.sleep(wait_time)
                n += 1

            pay_doc = db.payment_collection.find_one({"payment_id": payment_id})
            if pay_doc:
                if payment['status'] == 'succeeded':
                    db.update_payment_status(pay_doc["_id"], "paid")
                    logger.info(f'Покупка успешна: {payment["description"]}')
                    return {
                        "success": True,
                        "message": "Оплата прошла успешно"
                    }
                else:
                    db.update_payment_status(pay_doc["_id"], payment['status'])
                    return {
                        "success": False,
                        "message": 'Срок действия ссылки истек или произошла другая ошибка.'
                    }
            else:
                return {
                    "success": False,
                    "message": "Платеж не найден в базе данных."
                }

        except Exception as e:
            logger.error(f"Ошибка при проверке платежа: {str(e)}")
            raise  # Пробрасываем исключение для дальнейшей обработки



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
            return HttpResponse(status=400)

        pay_doc = db.payment_collection.find_one({"payment_id": payment_id})
        if not pay_doc:
            logger.error(f"Платеж с ID {payment_id} не найден в базе данных.")
            return HttpResponse(status=400)

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

        return HttpResponse(status=200)

    except Exception as e:
        logger.error(f"Ошибка при обработке уведомления вебхука: {str(e)}")
        return HttpResponse(status=400)  # Сообщаем кассе об ошибке
