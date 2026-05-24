import os
import re
import logging
from twilio.rest import Client as TwilioClient
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

logger = logging.getLogger(__name__)


def _is_us_phone(contact: str) -> bool:
    digits = re.sub(r"\D", "", contact)
    return (len(digits) == 10) or (len(digits) == 11 and digits[0] == "1")


def _normalize_phone(contact: str) -> str:
    digits = re.sub(r"\D", "", contact)
    if len(digits) == 10:
        return f"+1{digits}"
    return f"+{digits}"


def _build_message(
    confirmation_number: str,
    passenger_name: str,
    flight_id: str,
    airline: str,
    origin: str,
    destination: str,
    travel_date: str,
    departure_time: str,
    arrival_time: str,
    price: float,
) -> str:
    return (
        f"SkyLine Airways — Booking Confirmed!\n\n"
        f"Confirmation: {confirmation_number}\n"
        f"Passenger:    {passenger_name}\n"
        f"Flight:       {airline} {flight_id}\n"
        f"Route:        {origin} → {destination}\n"
        f"Date:         {travel_date}\n"
        f"Departure:    {departure_time}   Arrival: {arrival_time}\n"
        f"Total Paid:   ${price}\n\n"
        f"Thank you for choosing SkyLine Airways!\n"
        f"For changes or cancellations call 1-800-SKY-LINE."
    )


def send_confirmation(
    confirmation_number: str,
    passenger_name: str,
    contact_info: str,
    flight_id: str,
    airline: str,
    origin: str,
    destination: str,
    travel_date: str,
    departure_time: str,
    arrival_time: str,
    price: float,
) -> str:
    message = _build_message(
        confirmation_number, passenger_name, flight_id, airline,
        origin, destination, travel_date, departure_time, arrival_time, price,
    )

    contact = contact_info.strip()

    if _is_us_phone(contact):
        return _send_sms(_normalize_phone(contact), message, confirmation_number)
    elif "@" in contact:
        return _send_email(contact, confirmation_number, message)
    else:
        return (
            f"ERROR: Could not determine contact type for '{contact}'. "
            "Expected a US phone number (10 digits) or an email address."
        )


def _send_sms(to: str, body: str, confirmation: str) -> str:
    try:
        client = TwilioClient(
            os.environ["TWILIO_ACCOUNT_SID"],
            os.environ["TWILIO_AUTH_TOKEN"],
        )
        client.messages.create(
            body=body,
            from_=os.environ["TWILIO_PHONE_NUMBER"],
            to=to,
        )
        logger.info(f"SMS sent to {to} for booking {confirmation}")
        return f"SMS_SENT: Confirmation sent via SMS to {to}"
    except Exception as e:
        logger.error(f"SMS failed for {confirmation}: {e}")
        return f"SMS_ERROR: Failed to send SMS — {e}"


def _send_email(to: str, confirmation: str, body: str) -> str:
    try:
        sg = SendGridAPIClient(os.environ["SENDGRID_API_KEY"])
        mail = Mail(
            from_email=os.environ.get("SENDGRID_FROM_EMAIL", "bookings@skylineairways.com"),
            to_emails=to,
            subject=f"SkyLine Airways — Booking Confirmation {confirmation}",
            plain_text_content=body,
        )
        response = sg.send(mail)
        if response.status_code not in (200, 202):
            raise RuntimeError(f"SendGrid returned HTTP {response.status_code}")
        logger.info(f"Email sent to {to} for booking {confirmation}")
        return f"EMAIL_SENT: Confirmation sent via email to {to}"
    except Exception as e:
        logger.error(f"Email failed for {confirmation}: {e}")
        return f"EMAIL_ERROR: Failed to send email — {e}"
