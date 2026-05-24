import asyncio
import os
import json
import logging
from typing import Optional, AsyncIterator
import anthropic
from tools.airport import resolve_airport
from tools.flights import check_flights
from tools.booking import book_flight
from tools.notifications import send_confirmation

logger = logging.getLogger(__name__)

_client: Optional[anthropic.Anthropic] = None
_async_client: Optional[anthropic.AsyncAnthropic] = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    return _client


def _get_async_client() -> anthropic.AsyncAnthropic:
    global _async_client
    if _async_client is None:
        _async_client = anthropic.AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    return _async_client


SYSTEM_PROMPT = """You are Sky, the voice assistant for SkyLine Airways. You help customers search for flights and make bookings by phone.

## Ground Rules — Enforce Always
These prevent errors that cannot be undone:

1. **Never guess an airport code.** Every IATA code you use must come from a resolve_airport result. Not from memory, not from training data.
2. **Never invent or alter flight details.** Flight IDs, prices, departure times, arrival times, and seat counts must be quoted verbatim from the check_flights result.
3. **Never invent a confirmation number.** It must be copied character-for-character from the line "Confirmation Number: SKY-..." in the book_flight result.
4. **Never call book_flight until the customer explicitly confirms** — "yes", "go ahead", "confirm", "book it", or equivalent. A question like "that sounds good" is not confirmation.
5. **Never reuse details from a previous booking in the same conversation.** Each booking starts fresh.
6. **Never answer a policy question not listed in the Knowledge Base below.** Say: "I don't have that detail — our team can help at 1-800-SKY-LINE."

## Voice Style
- Short sentences. No filler phrases.
- Spell names and contact info back character by character when confirming.
- Speak numbers naturally: "6 AM" not "06:00", "two forty-nine dollars" or "$249" not "two-forty-nine dollars".

## Booking Flow — Follow in Strict Order

**Step 1 — Greet**
Ask how you can help. If they want a flight, move to Step 2.

**Step 2 — Route**
Ask for departure city, then destination city. Call resolve_airport for each one before moving on.
- `FOUND`: use the returned IATA code. Confirm aloud: "That's Los Angeles, LAX — correct?"
- `NEARBY`: read the suggested airports and distances. Ask which the customer prefers. Use that code.
- `NOT_FOUND`: ask the customer to spell the city or name a nearby major city. Do not proceed until both airports are resolved.

**Step 3 — Date**
Ask for the travel date. Repeat it back as a full calendar date ("July 15th, 2026") and ask them to confirm before calling check_flights.

**Step 4 — Search**
Call check_flights with the two IATA codes and date.
- Flights found: read each option using the exact airline name, flight ID, times, and price from the result. Do not paraphrase.
- `NO_FLIGHTS`: apologize. Offer to try a different date, or ask if they'd like to try a nearby departure airport.
- `DATE_ERROR`: read the reason and ask for a corrected date.

**Step 5 — Passenger details**
Ask the customer which option they want (use their answer to identify the exact flight ID from Step 4). Then collect:
- Full legal name as it appears on their government ID. Spell it back letter by letter to confirm.
- Contact info: US phone number (gets SMS) or email address (gets email). Read it back to confirm.

**Step 6 — Confirm**
Read back every detail using this exact structure — do not skip fields:
"To confirm: [full name] on [airline] flight [flight ID], from [origin] to [destination] on [date], departing [departure time] arriving [arrival time], total $[price]. Confirmation will go to [contact info]. Shall I go ahead and book?"
Wait for an explicit yes before continuing.

**Step 7 — Book**
Call book_flight. When the result starts with `BOOKING_CONFIRMED`, find the line "Confirmation Number: SKY-..." and read that code to the customer exactly.

**Step 8 — Notify**
Call send_confirmation immediately, passing every field from the flight result (Step 4) and the confirmation number (Step 7). Tell the customer whether SMS or email was sent. If it fails, read the confirmation number again and suggest they screenshot or write it down.

**Step 9 — Wrap up**
Ask if there is anything else. Wish them a great trip. End the call warmly.

## Tool Response Reference

| Result starts with | Meaning | What to do |
|---|---|---|
| `FOUND: XYZ —` | Airport matched | Use XYZ as the IATA code |
| `NEARBY: '...'` | City has no airport | Read options and distances; ask customer to choose |
| `NOT_FOUND:` | City not recognised | Ask customer to clarify or try another city |
| `Available flights from` | Flights found | Present options verbatim; record exact flight IDs |
| `NO_FLIGHTS:` | No service on route | Apologise; offer different date or nearby airport |
| `DATE_ERROR:` | Invalid or past date | Read the reason; ask for a new date |
| `BOOKING_CONFIRMED` | Booking succeeded | Extract and read the confirmation number verbatim |
| `SMS_SENT:` / `EMAIL_SENT:` | Notification delivered | Tell the customer |
| `SMS_ERROR:` / `EMAIL_ERROR:` | Notification failed | Apologise; read confirmation number again; suggest they write it down |
| `ERROR:` (any other) | Tool failed | Apologise; explain briefly; offer to retry once |

## Escalation
If the customer asks for a human agent, or if the same problem fails twice, say exactly: "I'll transfer you to a customer service specialist right now. Please hold." Then stop responding.

## Knowledge Base — Policies
Answer only from this list. For anything not here say: "I don't have that detail — our team can help at 1-800-SKY-LINE."

- **Cancellations**: Free within 24 h of booking. After 24 h: $75 fee. Non-refundable fares cannot be cancelled.
- **Changes**: $50 change fee plus any fare difference.
- **Baggage**: 1 carry-on included. First checked bag $35, second $50.
- **Check-in**: Opens 24 h before departure; closes 45 min before departure.
- **Refunds**: Refundable fares — returned to original payment in 7–10 business days. Non-refundable — travel credit issued instead.
- **Special assistance**: Request at least 48 h before departure by calling 1-800-SKY-LINE."""

TOOLS = [
    {
        "name": "resolve_airport",
        "description": "Convert a city name or airport name to an IATA airport code. Call this for BOTH the departure city and destination city before calling check_flights. Returns FOUND (direct match), NEARBY (city known but no airport — lists closest airports), or NOT_FOUND.",
        "input_schema": {
            "type": "object",
            "properties": {
                "city_name": {
                    "type": "string",
                    "description": "The city or airport name as provided by the customer (e.g. 'Los Angeles', 'LAX', 'New York', 'Heathrow')"
                }
            },
            "required": ["city_name"]
        }
    },
    {
        "name": "check_flights",
        "description": "Search for available flights between two airports on a given date. Returns up to 3 flight options with airline, flight number, times, and price. Returns NO_FLIGHTS if no routes exist.",
        "input_schema": {
            "type": "object",
            "properties": {
                "origin_iata": {
                    "type": "string",
                    "description": "IATA code for the departure airport (e.g. 'LAX')"
                },
                "destination_iata": {
                    "type": "string",
                    "description": "IATA code for the destination airport (e.g. 'JFK')"
                },
                "travel_date": {
                    "type": "string",
                    "description": "Travel date in YYYY-MM-DD format (e.g. '2026-07-15')"
                }
            },
            "required": ["origin_iata", "destination_iata", "travel_date"]
        }
    },
    {
        "name": "book_flight",
        "description": "Confirm a flight booking after the customer has chosen a flight and provided their details. Returns a confirmation number. Only call this AFTER the customer has verbally confirmed they want to proceed.",
        "input_schema": {
            "type": "object",
            "properties": {
                "flight_id": {
                    "type": "string",
                    "description": "The flight ID from the check_flights result (e.g. 'SKY101')"
                },
                "travel_date": {
                    "type": "string",
                    "description": "Travel date in YYYY-MM-DD format"
                },
                "passenger_name": {
                    "type": "string",
                    "description": "Full legal name of the passenger as it appears on their ID"
                },
                "contact_info": {
                    "type": "string",
                    "description": "US phone number (for SMS) or email address (for email) to send the confirmation to"
                }
            },
            "required": ["flight_id", "travel_date", "passenger_name", "contact_info"]
        }
    },
    {
        "name": "send_confirmation",
        "description": "Send the booking confirmation to the customer via SMS (US phone) or email. Call this immediately after book_flight succeeds.",
        "input_schema": {
            "type": "object",
            "properties": {
                "confirmation_number": {"type": "string", "description": "Confirmation number from book_flight (e.g. 'SKY-4B2XR7')"},
                "passenger_name": {"type": "string", "description": "Full name of the passenger"},
                "contact_info": {"type": "string", "description": "US phone number or email address"},
                "flight_id": {"type": "string", "description": "Flight ID (e.g. 'SKY101')"},
                "airline": {"type": "string", "description": "Airline name"},
                "origin": {"type": "string", "description": "Origin IATA code"},
                "destination": {"type": "string", "description": "Destination IATA code"},
                "travel_date": {"type": "string", "description": "Travel date in YYYY-MM-DD format"},
                "departure_time": {"type": "string", "description": "Departure time (e.g. '06:00')"},
                "arrival_time": {"type": "string", "description": "Arrival time (e.g. '14:30')"},
                "price": {"type": "number", "description": "Ticket price in USD"}
            },
            "required": [
                "confirmation_number", "passenger_name", "contact_info",
                "flight_id", "airline", "origin", "destination",
                "travel_date", "departure_time", "arrival_time", "price"
            ]
        }
    }
]

TOOL_HANDLERS = {
    "resolve_airport": resolve_airport,
    "check_flights": check_flights,
    "book_flight": book_flight,
    "send_confirmation": send_confirmation,
}

# In-memory session store: session_id -> list of message dicts
_sessions: dict[str, list[dict]] = {}


def _run_tool(name: str, tool_input: dict) -> str:
    handler = TOOL_HANDLERS.get(name)
    if not handler:
        return f"ERROR: Unknown tool '{name}'"
    try:
        return str(handler(**tool_input))
    except TypeError as e:
        return f"ERROR: Invalid parameters for {name}: {e}"
    except Exception as e:
        logger.error("Tool %s raised: %s", name, e)
        return f"ERROR: {e}"


def chat(session_id: str, user_message: str) -> str:
    client = _get_client()
    history = _sessions.setdefault(session_id, [])
    history.append({"role": "user", "content": user_message})

    while True:
        response = client.messages.create(
            model="claude-opus-4-7",
            max_tokens=4096,
            thinking={"type": "adaptive"},
            system=[
                {
                    "type": "text",
                    "text": SYSTEM_PROMPT,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            tools=TOOLS,
            messages=history,
        )

        logger.info("Session %s | stop_reason=%s | usage=%s", session_id, response.stop_reason, response.usage)

        # Append assistant turn (preserve full content list for tool_use blocks)
        history.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":
            # Extract the text response
            for block in response.content:
                if block.type == "text":
                    return block.text
            return ""

        if response.stop_reason == "tool_use":
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    result = _run_tool(block.name, block.input)
                    logger.info("Tool %s(%s) -> %s", block.name, block.input, result[:120])
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    })

            history.append({"role": "user", "content": tool_results})
            continue

        # Unexpected stop reason — return whatever text we have
        for block in response.content:
            if hasattr(block, "text"):
                return block.text
        return ""


async def chat_stream(session_id: str, user_message: str) -> AsyncIterator[str]:
    """Async generator that yields text tokens as they stream from Claude."""
    client = _get_async_client()
    history = _sessions.setdefault(session_id, [])
    history.append({"role": "user", "content": user_message})

    while True:
        async with client.messages.stream(
            model="claude-opus-4-7",
            max_tokens=4096,
            thinking={"type": "adaptive"},
            system=[
                {
                    "type": "text",
                    "text": SYSTEM_PROMPT,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            tools=TOOLS,
            messages=history,
        ) as stream:
            async for token in stream.text_stream:
                yield token
            response = await stream.get_final_message()

        history.append({"role": "assistant", "content": response.content})
        logger.info("Session %s | stop_reason=%s | usage=%s", session_id, response.stop_reason, response.usage)

        if response.stop_reason == "end_turn":
            break

        if response.stop_reason == "tool_use":
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    result = await asyncio.to_thread(_run_tool, block.name, block.input)
                    logger.info("Tool %s(%s) -> %s", block.name, block.input, result[:120])
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    })
            history.append({"role": "user", "content": tool_results})


def reset_session(session_id: str) -> None:
    _sessions.pop(session_id, None)


def list_sessions() -> list[str]:
    return list(_sessions.keys())
