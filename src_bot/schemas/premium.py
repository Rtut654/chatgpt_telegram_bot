from dataclasses import dataclass

from src_bot.config.payment_config import payment_config
from src_bot.bot.enums import PaymentType


@dataclass
class PremiumTariff:
    id: int
    desc: str


@dataclass
class Payment:
    type: str
    amount: float
    nominal: str
    desc: str
    price_id: str = None
    currency: str = "USD"

    def __str__(self):
        return f'{self.desc} - {self.amount} {self.nominal}'


payment_by_tariff = {
    '1': {
        PaymentType.stripe: Payment(
            type=PaymentType.stripe, amount=5.99, nominal="$", desc="🌎 Visa / Mastercard/ Apple/Google Pay",
            price_id=payment_config.STRIPE_PRICE_1),
        PaymentType.yookassa: Payment(type=PaymentType.yookassa, amount=600, nominal="RUB", desc="🟢 MIR cards"),
        PaymentType.cryptomus: Payment(type=PaymentType.cryptomus, amount=5.99, nominal="", desc="💎 Crypto"),
    },
    '6': {
        PaymentType.stripe: Payment(
            type=PaymentType.stripe, amount=24.99, nominal="$", desc="🌎 Visa / Mastercard/ Apple/Google Pay",
            price_id=payment_config.STRIPE_PRICE_1),
        PaymentType.yookassa: Payment(type=PaymentType.yookassa, amount=2500, nominal="RUB", desc="🟢 MIR cards"),
        PaymentType.cryptomus: Payment(type=PaymentType.cryptomus, amount=24.99, nominal="", desc="💎 Crypto"),
    },
    '12': {
        PaymentType.stripe: Payment(
            type=PaymentType.stripe, amount=44.99, nominal="$", desc="🌎 Visa / Mastercard/ Apple/Google Pay",
            price_id=payment_config.STRIPE_PRICE_1),
        PaymentType.yookassa: Payment(type=PaymentType.yookassa, amount=4500, nominal="RUB", desc="🟢 MIR cards"),
        PaymentType.cryptomus: Payment(type=PaymentType.cryptomus, amount=44.99, nominal="", desc="💎 Crypto"),
    },
}
