from enum import Enum


class CommandEnum(Enum):
    PREMIUM = (
        'premium',
        'premium description',
    )

    def __init__(self, command: str, description: str):
        self.command = command
        self.description = description


class CallbackQueryEnum(str, Enum):
    PREMIUM_VIEW = 'premium_view'
    PREMIUM_TARIFF = 'premium_tariff'
    PAYMENT_CHOOSE = 'PAYMENT_CHOOSE'

    def __str__(self):
        return self.value


class PaymentType(str, Enum):
    stripe = 'stripe'
    yookassa = 'yookassa'

    def __str__(self):
        return self.value
