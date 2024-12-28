import stripe

from src_bot.schemas.premium import Payment

from src_bot.config.payment_config import payment_config


async def process_payment(client_id: int, payment: Payment):
    stripe.api_key = payment_config.STRIPE_API_KEY
    session = stripe.checkout.Session.create(
        success_url="https://t.me/chatgpt_viral_bot",
        line_items=[{"price": payment.price_id, "quantity": 1}],
        automatic_tax={'enabled': False},
        allow_promotion_codes=True,
        client_reference_id=client_id,
        mode='subscription',
    )
    print(session.id)
    payment_link = session.url
    return payment_link
