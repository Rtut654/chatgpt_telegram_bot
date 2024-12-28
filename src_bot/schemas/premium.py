from dataclasses import dataclass

from src_bot.config.payment_config import payment_config


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

    def __str__(self):
        return f'{self.desc} - {self.amount} {self.nominal}'


payment_by_tariff = {
    '1': {
        'stripe': Payment(type="stripe", amount=5.99, nominal="$", desc="🌎 Visa / Mastercard/ Apple/Google Pay",
                          price_id=payment_config.STRIPE_PRICE_1),
        'yookassa': Payment(type="yookassa", amount=600, nominal="RUB", desc="🟢 MIR cards"),
    },
    '6': {
        'stripe': Payment(type="stripe", amount=24.99, nominal="$", desc="🌎 Visa / Mastercard/ Apple/Google Pay",
                          price_id=payment_config.STRIPE_PRICE_1),
        'yookassa': Payment(type="yookassa", amount=2500, nominal="RUB", desc="🟢 MIR cards"),
    },
    '12': {
        'stripe': Payment(type="stripe", amount=44.99, nominal="$", desc="🌎 Visa / Mastercard/ Apple/Google Pay",
                          price_id=payment_config.STRIPE_PRICE_1),
        'yookassa': Payment(type="yookassa", amount=4500, nominal="RUB", desc="🟢 MIR cards"),
    },
}
