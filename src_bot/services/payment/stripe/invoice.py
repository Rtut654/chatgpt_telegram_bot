import stripe

from src_bot.schemas.premium import Payment
from src_bot.config.payment_config import payment_config
from bot.database import get_database

stripe.api_key = payment_config.STRIPE_API_KEY


async def create_invoice(client_id: int, payment: Payment):
    session = stripe.checkout.Session.create(
        success_url=payment_config.URL_CALLBACK,
        line_items=[{"price": payment.price_id, "quantity": 1}],
        automatic_tax={'enabled': False},
        allow_promotion_codes=True,
        client_reference_id=client_id,
        mode='subscription',
    )
    print(session.id)
    payment_link = session.url
    db = get_database()

    db.add_new_payment(
        user_id=client_id,
        amount=payment.amount,
        currency=payment.nominal,
        payment_type="stripe",
        payment_id=session.invoice.id,
        order_id=None,
        status=session.status,
        additional_data={"uuid": session.id, "url": session.url}
    )
    return payment_link
