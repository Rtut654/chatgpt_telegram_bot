import config
import json
import logging
import asyncio

from yookassa import Configuration, Payment

Configuration.account_id = config.account_id
Configuration.secret_key = config.secret_key
return_tg_url = config.return_tg_url

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