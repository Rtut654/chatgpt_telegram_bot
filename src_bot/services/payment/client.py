from flask import Flask, jsonify, request
from src_bot.config.payment_config import payment_config
import src_bot.services.payment.stripe.webhook as stripe

app = Flask(__name__)


# logger = logging.getLogger('werkzeug') # grabs underlying WSGI logger
# handler = logging.FileHandler('/var/log/bot/access.log') # creates handler for the log file
# logger.addHandler(handler)

@app.route('/')
def hello():
    return "Hello, HTTPS!"


@app.route("/stripe_webhook", methods=['POST'])
def stripe_webhook():
    result = stripe.webhook(request)
    return result


def run_client():
    context = (
        payment_config.SSL_CERT_PATH,
        payment_config.SSL_KEY_PATH,
    )

    app.run(
        host='0.0.0.0',
        port=4433,
        # debug=True,
        ssl_context=context,
    )


if __name__ == "__main__":
    run_client()
