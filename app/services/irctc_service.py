def search_trains(source: str, destination: str):
    return [
        {
            "train_name": "Rajdhani Express",
            "train_number": "12301",
            "departure": "18:00",
            "arrival": "06:00"
        },
        {
            "train_name": "Shatabdi Express",
            "train_number": "12002",
            "departure": "07:00",
            "arrival": "13:00"
        }
    ]


def check_availability(train_number: str):
    return {
        "train_number": train_number,
        "SL": "Available 45",
        "3AC": "WL 12",
        "2AC": "Available 10"
    }


def cancellation_policy():
    return """
    IRCTC Cancellation Policy:
    - 48 hrs before departure: 25% deduction
    - 12–48 hrs: 50% deduction
    - Less than 12 hrs: No refund
    """