import os

from pydantic_settings import BaseSettings, SettingsConfigDict

script_dir = os.path.dirname(os.path.abspath(__file__))
env_file_path = os.path.join(script_dir, 'payment.env')


class PaymentSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=env_file_path, env_file_encoding='utf-8'
    )
    URL_CALLBACK: str = "https://t.me/chatgpt_viral_bot"

    STRIPE_API_KEY: str = os.getenv("STRIPE_API_KEY")
    STRIPE_PRICE_1: str = os.getenv("STRIPE_PRICE_1")

    YOOKASSA_CLIENT_ID: str = os.getenv("YOOKASSA_CLIENT_ID")
    YOOKASSA_SECRET_KEY: str = os.getenv("YOOKASSA_SECRET_KEY")

    CRYPTOMUS_MERCHANT_UUID: str = os.getenv("CRYPTOMUS_MERCHANT_UUID")
    CRYPTOMUS_API_KEY: str = os.getenv("CRYPTOMUS_API_KEY")

    WEBHOOK_SSL_CERT_PATH: str = os.getenv("WEBHOOK_SSL_CERT_PATH")
    WEBHOOK_SSL_CERT_KEY: str = os.getenv("WEBHOOK_SSL_CERT_KEY")


payment_config = PaymentSettings()
