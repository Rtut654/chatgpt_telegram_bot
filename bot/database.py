from typing import Optional, Any
from datetime import datetime, timedelta

import pymongo
import uuid
from datetime import datetime

import config


class Database:
    def __init__(self):
        self.client = pymongo.MongoClient(config.mongodb_uri)
        self.db = self.client["chatgpt_telegram_bot"]

        self.user_collection = self.db["user"]
        self.dialog_collection = self.db["dialog"]
        self.payment_collection = self.db["payments"]

    def check_if_user_exists(self, user_id: int, raise_exception: bool = False):
        if self.user_collection.count_documents({"_id": user_id}) > 0:
            return True
        else:
            if raise_exception:
                raise ValueError(f"User {user_id} does not exist")
            else:
                return False

    def add_new_user(
        self,
        user_id: int,
        chat_id: int,
        username: str = "",
        first_name: str = "",
        last_name: str = "",
    ):
        user_dict = {
            "_id": user_id,
            "chat_id": chat_id,

            "username": username,
            "first_name": first_name,
            "last_name": last_name,

            "last_interaction": datetime.now(),
            "first_seen": datetime.now(),

            "current_dialog_id": None,
            "current_chat_mode": "assistant",
            "current_model": config.models["available_text_models"][0],

            "n_used_tokens": {},

            "n_generated_images": 0,
            "n_transcribed_seconds": 0.0,  # voice message transcription
            "is_subscribed": False,
            "subscription_expire_date": None
        }

        if not self.check_if_user_exists(user_id):
            self.user_collection.insert_one(user_dict)

    def start_new_dialog(self, user_id: int):
        self.check_if_user_exists(user_id, raise_exception=True)

        dialog_id = str(uuid.uuid4())
        dialog_dict = {
            "_id": dialog_id,
            "user_id": user_id,
            "chat_mode": self.get_user_attribute(user_id, "current_chat_mode"),
            "start_time": datetime.now(),
            "model": self.get_user_attribute(user_id, "current_model"),
            "messages": []
        }

        # add new dialog
        self.dialog_collection.insert_one(dialog_dict)

        # update user's current dialog
        self.user_collection.update_one(
            {"_id": user_id},
            {"$set": {"current_dialog_id": dialog_id}}
        )

        return dialog_id

    def get_user_attribute(self, user_id: int, key: str):
        self.check_if_user_exists(user_id, raise_exception=True)
        user_dict = self.user_collection.find_one({"_id": user_id})

        if key not in user_dict:
            return None

        return user_dict[key]

    def set_user_attribute(self, user_id: int, key: str, value: Any):
        self.check_if_user_exists(user_id, raise_exception=True)
        self.user_collection.update_one({"_id": user_id}, {"$set": {key: value}})

    def update_n_used_tokens(self, user_id: int, model: str, n_input_tokens: int, n_output_tokens: int):
        n_used_tokens_dict = self.get_user_attribute(user_id, "n_used_tokens")

        if model in n_used_tokens_dict:
            n_used_tokens_dict[model]["n_input_tokens"] += n_input_tokens
            n_used_tokens_dict[model]["n_output_tokens"] += n_output_tokens
        else:
            n_used_tokens_dict[model] = {
                "n_input_tokens": n_input_tokens,
                "n_output_tokens": n_output_tokens
            }

        self.set_user_attribute(user_id, "n_used_tokens", n_used_tokens_dict)

    def get_dialog_messages(self, user_id: int, dialog_id: Optional[str] = None):
        self.check_if_user_exists(user_id, raise_exception=True)

        if dialog_id is None:
            dialog_id = self.get_user_attribute(user_id, "current_dialog_id")

        dialog_dict = self.dialog_collection.find_one({"_id": dialog_id, "user_id": user_id})
        return dialog_dict["messages"]

    def set_dialog_messages(self, user_id: int, dialog_messages: list, dialog_id: Optional[str] = None):
        self.check_if_user_exists(user_id, raise_exception=True)

        if dialog_id is None:
            dialog_id = self.get_user_attribute(user_id, "current_dialog_id")

        self.dialog_collection.update_one(
            {"_id": dialog_id, "user_id": user_id},
            {"$set": {"messages": dialog_messages}}
        )

    def add_new_payment(self, user_id: int,
                        amount: float,
                        currency: str,
                        payment_type: str,
                        payment_id: Optional[str] = None,
                        order_id: Optional[str] = None,
                        status: str = "pending",
                        additional_data: Optional[dict] = None) -> str:
        """
        Добавляет новый платеж в базу данных.

        Аргументы:
            user_id (int): Идентификатор пользователя, совершающего платеж.
            amount (float): Сумма платежа.
            currency (str): Валюта платежа, например "RUB" или "USDT".
            payment_type (str): Тип платежной системы, например "yookassa" или "cryptomus".
            payment_id (str, опционально): Идентификатор платежа во внешней системе.
            order_id (str, опционально): Идентификатор заказа во внешней системе.
            status (str, опционально): Статус платежа, по умолчанию "pending" (ожидается).
            additional_data (dict, опционально): Дополнительная информация о платеже.

        Возвращает:
            str: ID добавленного платежа.
        """
        self.check_if_user_exists(user_id, raise_exception=True)

        pay_id = str(uuid.uuid4())
        payment_doc = {
            "_id": pay_id,
            "user_id": user_id,
            "amount": amount,
            "currency": currency,
            "payment_type": payment_type,
            "payment_id": payment_id,
            "order_id": order_id,
            "status": status,
            "additional_data": additional_data if additional_data else {},
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }

        self.payment_collection.insert_one(payment_doc)
        return pay_id

    def get_payment_by_id(self, pay_id: str) -> Optional[dict]:
        """
        Получает данные о платеже по его внутреннему ID.

        Аргументы:
            pay_id (str): Внутренний ID платежа в базе данных.

        Возвращает:
            Optional[dict]: Документ с информацией о платеже или None, если платеж не найден.
        """
        return self.payment_collection.find_one({"_id": pay_id})

    def update_payment_status(self, pay_id: str, new_status: str):
        """
        Обновляет статус платежа.

        Аргументы:
            pay_id (str): Внутренний ID платежа, статус которого нужно обновить.
            new_status (str): Новый статус платежа, например "paid", "failed", "expired".

        Возвращает:
            None
        """
        self.payment_collection.update_one(
            {"_id": pay_id},
            {"$set": {"status": new_status, "updated_at": datetime.now()}}

        )
    def update_user_subscription(self, user_id: int, duration_days: int = 30):
        """
        Активирует подписку для пользователя на указанный период.

        Args:
            user_id (int): Идентификатор пользователя.
            duration_days (int): Кол-во дней подписки. По умолчанию 30.
        """
        subscription_end = datetime.now() + timedelta(days=duration_days)
        self.user_collection.update_one(
            {"_id": user_id},
            {
                "$set": {
                    "is_subscribed": True,
                    "subscription_expire_date": subscription_end
                }
            }
        )
    # def set_payment_external_ids(self, pay_id: str, payment_id: Optional[str] = None, order_id: Optional[str] = None):
    #     """
    #     Устанавливает внешние идентификаторы платежа, если они стали известны после создания записи.
    #
    #     Аргументы:
    #         pay_id (str): Внутренний ID платежа.
    #         payment_id (str, опционально): Идентификатор платежа во внешней системе.
    #         order_id (str, опционально): Идентификатор заказа во внешней системе.
    #
    #     Возвращает:
    #         None
    #     """
    #     update_fields = {"updated_at": datetime.now()}
    #     if payment_id:
    #         update_fields["payment_id"] = payment_id
    #     if order_id:
    #         update_fields["order_id"] = order_id
    #
    #     self.payment_collection.update_one({"_id": pay_id}, {"$set": update_fields})
    #
    # def append_payment_additional_data(self, pay_id: str, data: dict):
    #     """
    #     Добавляет или обновляет данные в additional_data платежа.
    #
    #     Аргументы:
    #         pay_id (str): Внутренний ID платежа.
    #         data (dict): Словарь, который будет добавлен или обновлен в additional_data.
    #
    #     Возвращает:
    #         None
    #     """
    #     self.payment_collection.update_one(
    #         {"_id": pay_id},
    #         {"$set": {f"additional_data.{k}": v for k, v in data.items()}, "$currentDate": {"updated_at": True}}
    #     )