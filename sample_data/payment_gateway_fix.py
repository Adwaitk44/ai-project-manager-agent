def validate_payment_response(response):
    if response is None:
        return False

    return response.get("status") == "success"