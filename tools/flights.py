from datetime import date, datetime

# Keyed by (ORIGIN_IATA, DESTINATION_IATA).
# AAL → YVR is intentionally absent to trigger the no-flights error case.
MOCK_FLIGHTS: dict[tuple[str, str], list[dict]] = {
    ("LAX", "JFK"): [
        {"flight_id": "SKY101", "airline": "SkyLine Airways", "departure": "06:00", "arrival": "14:30", "duration": "5h 30m", "price": 249, "seats": 18},
        {"flight_id": "SKY103", "airline": "SkyLine Airways", "departure": "11:00", "arrival": "19:30", "duration": "5h 30m", "price": 299, "seats": 7},
        {"flight_id": "UA756", "airline": "United Airlines",   "departure": "14:30", "arrival": "23:15", "duration": "5h 45m", "price": 279, "seats": 22},
    ],
    ("JFK", "LAX"): [
        {"flight_id": "SKY102", "airline": "SkyLine Airways", "departure": "07:00", "arrival": "10:30", "duration": "5h 30m", "price": 249, "seats": 15},
        {"flight_id": "SKY104", "airline": "SkyLine Airways", "departure": "13:00", "arrival": "16:30", "duration": "5h 30m", "price": 319, "seats": 4},
        {"flight_id": "DL890",  "airline": "Delta Air Lines",  "departure": "17:00", "arrival": "20:45", "duration": "5h 45m", "price": 289, "seats": 11},
    ],
    ("LAX", "SFO"): [
        {"flight_id": "SKY201", "airline": "SkyLine Airways", "departure": "08:00", "arrival": "09:15", "duration": "1h 15m", "price": 89,  "seats": 30},
        {"flight_id": "SKY203", "airline": "SkyLine Airways", "departure": "12:00", "arrival": "13:15", "duration": "1h 15m", "price": 99,  "seats": 25},
        {"flight_id": "SKY205", "airline": "SkyLine Airways", "departure": "18:00", "arrival": "19:15", "duration": "1h 15m", "price": 79,  "seats": 8},
    ],
    ("SFO", "LAX"): [
        {"flight_id": "SKY202", "airline": "SkyLine Airways", "departure": "09:30", "arrival": "10:45", "duration": "1h 15m", "price": 89,  "seats": 28},
        {"flight_id": "SKY204", "airline": "SkyLine Airways", "departure": "14:00", "arrival": "15:15", "duration": "1h 15m", "price": 99,  "seats": 15},
    ],
    ("JFK", "LHR"): [
        {"flight_id": "SKY401", "airline": "SkyLine Airways", "departure": "21:00", "arrival": "09:00+1", "duration": "7h 00m", "price": 649, "seats": 20},
        {"flight_id": "BA178",  "airline": "British Airways",  "departure": "19:00", "arrival": "07:00+1", "duration": "7h 00m", "price": 789, "seats": 12},
    ],
    ("LHR", "JFK"): [
        {"flight_id": "SKY402", "airline": "SkyLine Airways", "departure": "10:00", "arrival": "13:00", "duration": "8h 00m", "price": 649, "seats": 18},
        {"flight_id": "BA175",  "airline": "British Airways",  "departure": "11:00", "arrival": "14:00", "duration": "8h 00m", "price": 799, "seats": 9},
    ],
    ("LAX", "YVR"): [
        {"flight_id": "SKY301", "airline": "SkyLine Airways", "departure": "09:00", "arrival": "11:30", "duration": "2h 30m", "price": 189, "seats": 22},
        {"flight_id": "AC562",  "airline": "Air Canada",       "departure": "14:00", "arrival": "16:30", "duration": "2h 30m", "price": 219, "seats": 14},
    ],
    ("YVR", "LAX"): [
        {"flight_id": "SKY302", "airline": "SkyLine Airways", "departure": "12:00", "arrival": "14:30", "duration": "2h 30m", "price": 189, "seats": 20},
    ],
    ("SEA", "YVR"): [
        {"flight_id": "SKY311", "airline": "SkyLine Airways", "departure": "10:00", "arrival": "11:00", "duration": "1h 00m", "price": 129, "seats": 35},
        {"flight_id": "SKY313", "airline": "SkyLine Airways", "departure": "17:00", "arrival": "18:00", "duration": "1h 00m", "price": 109, "seats": 18},
    ],
    ("ATL", "MIA"): [
        {"flight_id": "SKY501", "airline": "SkyLine Airways", "departure": "08:30", "arrival": "10:00", "duration": "1h 30m", "price": 119, "seats": 25},
        {"flight_id": "SKY503", "airline": "SkyLine Airways", "departure": "15:00", "arrival": "16:30", "duration": "1h 30m", "price": 139, "seats": 10},
    ],
    ("MIA", "ATL"): [
        {"flight_id": "SKY502", "airline": "SkyLine Airways", "departure": "11:00", "arrival": "12:30", "duration": "1h 30m", "price": 119, "seats": 20},
        {"flight_id": "AA2201", "airline": "American Airlines", "departure": "16:00", "arrival": "17:30", "duration": "1h 30m", "price": 149, "seats": 8},
    ],
    ("DFW", "LAX"): [
        {"flight_id": "SKY601", "airline": "SkyLine Airways",  "departure": "07:00", "arrival": "08:30", "duration": "2h 30m", "price": 159, "seats": 30},
        {"flight_id": "AA1234", "airline": "American Airlines", "departure": "12:00", "arrival": "13:45", "duration": "2h 45m", "price": 179, "seats": 15},
    ],
    ("LAX", "DFW"): [
        {"flight_id": "SKY602", "airline": "SkyLine Airways", "departure": "10:00", "arrival": "15:00", "duration": "3h 00m", "price": 159, "seats": 28},
        {"flight_id": "SKY604", "airline": "SkyLine Airways", "departure": "16:00", "arrival": "21:00", "duration": "3h 00m", "price": 179, "seats": 12},
    ],
    ("LAX", "NRT"): [
        {"flight_id": "SKY701", "airline": "SkyLine Airways", "departure": "13:00", "arrival": "17:00+1", "duration": "11h 00m", "price": 899, "seats": 14},
        {"flight_id": "JL062",  "airline": "Japan Airlines",   "departure": "17:00", "arrival": "21:00+1", "duration": "11h 00m", "price": 1049, "seats": 6},
    ],
    ("YYZ", "LHR"): [
        {"flight_id": "SKY801", "airline": "SkyLine Airways", "departure": "20:00", "arrival": "08:00+1", "duration": "7h 00m", "price": 599, "seats": 16},
        {"flight_id": "AC856",  "airline": "Air Canada",       "departure": "22:00", "arrival": "10:00+1", "duration": "7h 00m", "price": 689, "seats": 9},
    ],
}

# Flat lookup by flight_id so booking can retrieve full details
ALL_FLIGHTS: dict[str, dict] = {}
for (origin, dest), flights in MOCK_FLIGHTS.items():
    for f in flights:
        ALL_FLIGHTS[f["flight_id"]] = {**f, "origin": origin, "destination": dest}


def _validate_date(travel_date: str) -> tuple[bool, str]:
    try:
        parsed = datetime.strptime(travel_date, "%Y-%m-%d").date()
    except ValueError:
        return False, f"Invalid date format '{travel_date}'. Please use YYYY-MM-DD (e.g. 2026-06-15)."

    today = date.today()
    max_date = date(today.year + 1, today.month, today.day)

    if parsed < today:
        return False, f"The date {travel_date} is in the past. Please provide a date from today ({today}) onward."
    if parsed > max_date:
        return False, f"The date {travel_date} is more than one year away. Bookings are only available within the next 12 months."

    return True, ""


def check_flights(origin_iata: str, destination_iata: str, travel_date: str) -> str:
    valid, error = _validate_date(travel_date)
    if not valid:
        return f"DATE_ERROR: {error}"

    origin = origin_iata.strip().upper()
    destination = destination_iata.strip().upper()

    flights = MOCK_FLIGHTS.get((origin, destination))
    if not flights:
        return (
            f"NO_FLIGHTS: No flights found from {origin} to {destination} on {travel_date}. "
            "You can offer the customer an alternative date or a different route."
        )

    lines = [f"Available flights from {origin} to {destination} on {travel_date}:"]
    for i, f in enumerate(flights, 1):
        lines.append(
            f"Option {i}: {f['airline']} Flight {f['flight_id']} | "
            f"Departs {f['departure']} → Arrives {f['arrival']} ({f['duration']}) | "
            f"${f['price']} | {f['seats']} seats left"
        )

    return "\n".join(lines)
