import requests


def ping():
    url = "https://localhost:4433"

    try:
        response = requests.get(url, verify=False)
        if response.status_code == 200:
            print(f"Service {url} is available.")
        else:
            print(f"Service {url} is not available. Status code: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Service {url} is not available. Error: {e}")


def test_stripe_webhook():
    url = 'https://localhost:4433/stripe_webhook'

    payload = {
        "id": "evt_test_webhook",
        "object": "event",
        "type": "payment_intent.succeeded",
        "data": {
            "object": {
                "id": "pi_test",
                "object": "payment_intent",
                "amount": 2000,
                "currency": "usd",
                "status": "succeeded"
            }
        }
    }

    headers = {
        "Content-Type": "application/json",
        "Stripe-Signature": "t_test_signature"
    }

    response = requests.post(url, json=payload, headers=headers, verify=False)
    assert response.status_code == 200, f"Expected status code 200, but got {response.status_code}"
    print(response.text)


test_stripe_webhook()
