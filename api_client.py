import requests

BASE_URL = "http://127.0.0.1:8001"

def park_vehicle(plate_number, bay_number):

    payload = {
        "plate_number": plate_number,
        "bay_number": bay_number
    }

    response = requests.post(
        f"{BASE_URL}/park_vehicle",
        json=payload
    )

    return response.json()