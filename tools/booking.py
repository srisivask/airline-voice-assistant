import random
import string
from typing import Optional
from tools.flights import ALL_FLIGHTS

# In-memory store — fine for demo; swap for a DB in production
BOOKINGS: dict[str, dict] = {}


def _generate_confirmation() -> str:
    suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"SKY-{suffix}"


def book_flight(flight_id: str, travel_date: str, passenger_name: str, contact_info: str) -> str:
    flight = ALL_FLIGHTS.get(flight_id.strip().upper())
    if not flight:
        return f"ERROR: Flight '{flight_id}' not found. Please check the flight ID and try again."

    confirmation = _generate_confirmation()

    BOOKINGS[confirmation] = {
        "confirmation_number": confirmation,
        "flight_id": flight["flight_id"],
        "airline": flight["airline"],
        "origin": flight["origin"],
        "destination": flight["destination"],
        "travel_date": travel_date,
        "departure_time": flight["departure"],
        "arrival_time": flight["arrival"],
        "price": flight["price"],
        "passenger_name": passenger_name,
        "contact_info": contact_info,
    }

    return (
        f"BOOKING_CONFIRMED\n"
        f"Confirmation Number: {confirmation}\n"
        f"Passenger: {passenger_name}\n"
        f"Flight: {flight['airline']} {flight['flight_id']}\n"
        f"Route: {flight['origin']} → {flight['destination']}\n"
        f"Date: {travel_date}\n"
        f"Departs: {flight['departure']} | Arrives: {flight['arrival']}\n"
        f"Total: ${flight['price']}"
    )


def get_booking(confirmation_number: str) -> Optional[dict]:
    return BOOKINGS.get(confirmation_number.strip().upper())
