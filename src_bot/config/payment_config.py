import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class PaymentSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='/payment.env', env_file_encoding='utf-8'
    )
    URL_CALLBACK: str = "https://t.me/chatgpt_viral_bot"

    STRIPE_API_KEY: str = os.getenv("STRIPE_API_KEY")
    STRIPE_PRICE_1: str = os.getenv("STRIPE_PRICE_1")

    YOOKASSA_CLIENT_ID: str = os.getenv("YOOKASSA_CLIENT_ID")
    YOOKASSA_SECRET_KEY: str = os.getenv("YOOKASSA_SECRET_KEY")

    CRYPTOMUS_MERCHANT_UUID: str = os.getenv("CRYPTOMUS_MERCHANT_UUID")
    CRYPTOMUS_API_KEY: str = os.getenv("CRYPTOMUS_API_KEY")

    SSL_CERT_PATH: str = "ssl/cert.pem"
    SSL_KEY_PATH: str = "ssl/key.pem"


payment_config = PaymentSettings()
