import stripe

from src_bot.config.payment_config import payment_config
from bot.database import get_database

endpoint_secret = "payment_config."
stripe.api_key = payment_config.STRIPE_API_KEY


# logger = logging.getLogger('werkzeug') # grabs underlying WSGI logger
# handler = logging.FileHandler('/var/log/bot/access.log') # creates handler for the log file
# logger.addHandler(handler)

def webhook(request):
    event = None
    customer_id = None
    payload = request.data
    sig_header = request.headers['STRIPE_SIGNATURE']
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
        print('Stripe event type - ', event['type'])
        if event['type'] not in ['checkout.session.completed', 'invoice.payment_succeeded']:
            return "OK"

        # this one comes only on sub creation
        if event['type'] == 'checkout.session.completed':
            notify = True
            session = event['data']['object']
            customer_id = event['data']['object']['customer']
            subscription_id = event['data']['object']['subscription']
            chat_id = session['client_reference_id']
            session = stripe.checkout.Session.retrieve(
                event['data']['object']['id'],
                expand=['line_items'],
            )
            line_items = session.line_items
            price_id = line_items["data"][0]["price"]["id"]
            update = True
            if "web" in event['data']['object']['metadata']:
                # TODO: добавить словарь price_id_to_duration, но лучше хранить в монге duration по payment_id
                duration = 30
                # activate subscription with the following parameters {chat_id} {duration} {subscription_id} {customer_id} {update}

        # this one comes when subs is updateds
        elif event['type'] == 'invoice.payment_succeeded':
            session = event['data']['object']
            customer_id = session['customer']
            subscription_id = event['data']['object']['subscription']
            price_id = session['lines']['data'][0]['plan']['id']
            chat_id = session['client_reference_id']

            db = get_database()
            print(subscription_id, customer_id, price_id)
            db.update_user_subscription(chat_id=chat_id, duration_days=30)

    except ValueError as e:
        # Invalid payload
        raise e
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        raise e

    return "OK"
