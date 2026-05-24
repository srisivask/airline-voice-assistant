# SkyLine Airways — AI Voice Assistant

A FastAPI backend powering a multi-turn airline booking agent built on the Anthropic API (`claude-opus-4-7`), with a streaming chat UI and a Phonely voice integration.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Project Structure](#project-structure)
3. [How the Agent Was Built](#how-the-agent-was-built)
4. [Functionalities](#functionalities)
5. [Improvements Made](#improvements-made)
6. [Setup](#setup)
7. [Running the Agent](#running-the-agent)
8. [Phonely Voice Integration](#phonely-voice-integration)
9. [API Reference](#api-reference)
10. [Testing](#testing)

---

## Architecture Overview

```
Browser / Phonely
       │
       ▼
  FastAPI (main.py)
  ├── POST /chat        ← streaming AI agent (SSE)
  ├── POST /tools       ← Phonely webhook (tool execution only)
  ├── GET  /agent       ← chat UI
  └── GET  /            ← step-by-step booking UI
       │
       ▼
  agent.py  (Anthropic SDK — claude-opus-4-7)
  ├── Agentic loop with tool use
  ├── Per-session conversation history
  ├── Adaptive thinking
  └── SSE token streaming
       │
       ▼
  tools/
  ├── airport.py        ← IATA resolution + nearby airport suggestions
  ├── flights.py        ← mock flight search + date validation
  ├── booking.py        ← booking store + confirmation numbers
  └── notifications.py  ← Twilio SMS + SendGrid email
```

---

## Project Structure

```
airline-voice-assistant/
├── main.py                    # FastAPI app, routes, SSE endpoint
├── agent.py                   # Claude agent — agentic loop, streaming, session history
├── tools/
│   ├── airport.py             # City/IATA resolution with nearby airport fallback
│   ├── flights.py             # Mock flight data, route search, date validation
│   ├── booking.py             # In-memory booking store, SKY-XXXXXX confirmation numbers
│   └── notifications.py       # Twilio SMS (US phones) + SendGrid email
├── static/
│   ├── index.html             # Step-by-step booking UI (no framework)
│   └── agent.html             # Streaming chat UI
├── phonely/
│   ├── system_prompt.md       # Prompt to paste into Phonely
│   ├── tools_config.json      # Tool schemas for Phonely Actions
│   └── knowledge_base.md      # Policy document for Phonely Knowledge Base
├── .env.example
└── requirements.txt
```

---

## How the Agent Was Built

### 1. Tool layer (`tools/`)

Four pure Python functions that the agent can call. Each returns a plain string with a prefix (`FOUND:`, `NO_FLIGHTS:`, `BOOKING_CONFIRMED`, etc.) so both the LLM and the JavaScript frontend can parse them consistently.

| Tool | What it does |
|---|---|
| `resolve_airport(city_name)` | Looks up a city or IATA code; falls back to nearest-airport suggestions using the haversine formula |
| `check_flights(origin_iata, destination_iata, travel_date)` | Searches mock flight data; validates that the date is today or later and within 12 months |
| `book_flight(flight_id, travel_date, passenger_name, contact_info)` | Creates an in-memory booking and generates a `SKY-XXXXXX` confirmation number |
| `send_confirmation(...)` | Routes to Twilio SMS for US phone numbers or SendGrid email otherwise |

### 2. Agentic loop (`agent.py`)

The agent is a **manual tool-use loop** built on the Anthropic Python SDK:

```
while True:
    stream response from Claude
    yield text tokens to client as they arrive
    collect full response via get_final_message()

    if stop_reason == "end_turn":
        break

    if stop_reason == "tool_use":
        run each requested tool
        append tool results to conversation history
        continue loop
```

Key design decisions:
- **Async streaming** — uses `AsyncAnthropic` and `client.messages.stream()` so text tokens are forwarded to the browser as they are generated, not after the full response is ready.
- **Per-session history** — each browser tab gets a UUID session ID; the full message list (including tool-use and tool-result turns) is kept in a server-side `dict` and passed to Claude on every call. This gives Claude memory of the entire booking conversation.
- **Prompt caching** — the system prompt is marked with `cache_control: {type: "ephemeral"}`, so Anthropic's servers cache it across turns in the same session, reducing latency and cost on repeated calls.
- **Tool execution in threads** — tool functions are synchronous (some make network calls); they are run with `asyncio.to_thread` so they do not block the async event loop.

### 3. Streaming endpoint (`main.py`)

`POST /chat` returns a `StreamingResponse` with `Content-Type: text/event-stream`. Each text token from the agent is sent as an SSE event:

```
data: {"t": "Hello"}\n\n
data: {"t": "!"}\n\n
data: [DONE]\n\n
```

Errors are sent as `data: {"error": "..."}` before `[DONE]`.

### 4. Chat UI (`static/agent.html`)

A self-contained HTML/CSS/JS page (no framework). Uses the browser's `fetch` + `ReadableStream` API to read the SSE response chunk by chunk, parse `data:` lines, and append each token to a live message bubble as it arrives. The typing indicator stays visible until the first token lands.

### 5. Phonely integration (`POST /tools`)

A separate webhook endpoint handles Phonely's tool-call requests. Phonely sends a JSON payload when its LLM decides to call a tool; this endpoint executes the same tool functions and returns the result. Supports three payload shapes Phonely may use:

```json
{"name": "check_flights", "parameters": {...}}
{"function": {"name": "check_flights", "arguments": "{...}"}}
{"tool_name": "check_flights", "parameters": {...}}
```

---

## Functionalities

### Airport resolution
- Resolves 30+ cities and their common aliases (e.g. "New York", "JFK", "new york city" all → JFK).
- Partial match handles informal names like "San Fran" → SFO.
- **Nearby airport suggestions**: if the customer names a city with no airport (Beverly Hills, Scottsdale, Brooklyn, Kyoto, etc.), the tool calculates distances to all served airports using the haversine formula and returns the three closest with distances in km.

### Flight search
- 15 routes across North America, Europe, and Asia-Pacific with 2–3 flight options each.
- Returns airline name, flight ID, departure/arrival times, duration, price, and seats remaining.
- Date validation: rejects past dates and dates more than 12 months out with a clear error message.
- Intentional no-flights route (Aalborg → Vancouver) for testing the error path.

### Booking
- Generates a unique `SKY-XXXXXX` confirmation number (random alphanumeric suffix).
- Stores booking in an in-memory dict keyed by confirmation number.
- Booking details include all flight fields plus passenger name, contact info, and travel date.

### Notifications
- Detects US phone numbers (10-digit or 11-digit starting with 1) and sends SMS via Twilio.
- Sends email via SendGrid for all other contact info.
- Graceful degradation: if credentials are missing, returns an error string instead of crashing; the booking itself is still saved.

### Conversation memory
- Full message history (user, assistant, tool-use, tool-result turns) is stored per session.
- Claude sees the entire conversation on every turn, so it never forgets a flight the customer chose or a name they gave earlier.

### Error handling
- Unknown airport → asks customer to clarify
- City with no airport → suggests nearest served airports
- No flights on route → offers alternative dates or nearby departure airports
- Invalid/past date → explains why and asks for a new one
- Tool execution failure → tells the customer gracefully, offers to retry
- Notification failure → reads the confirmation number again and suggests writing it down

### Policy knowledge base
Built into the system prompt: cancellation fees, change fees, baggage allowances, check-in windows, refund timelines, and special assistance procedures. Agent is explicitly instructed not to answer policy questions outside this list.

### Human escalation
If the customer asks for a human agent, or the same issue fails twice, the agent transfers the call.

---

## Improvements Made

### 1. Model upgrade: `claude-sonnet-4-6` → `claude-opus-4-7`

Opus 4.7 is significantly stronger at multi-turn tool-use flows. In practice this means fewer wrong tool calls, better recovery when a tool returns an error, and more natural conversation — it knows when to ask a clarifying question versus when to proceed.

### 2. Adaptive thinking

`thinking: {type: "adaptive"}` was added to every API call. Before generating a response, the model silently reasons through the conversation state. For a booking flow this matters: the model is less likely to hallucinate a confirmation number, forget which flight the customer chose, or call tools in the wrong order. Adaptive means thinking is only applied when the turn is complex enough to warrant it, so simple replies have no extra cost.

`max_tokens` was raised from 1024 to 4096 to give the thinking process adequate budget alongside the visible response.

### 3. Streaming responses (SSE)

The `/chat` endpoint now streams tokens as they are generated rather than waiting for the full response. The browser renders each token as it arrives, turning a 3–5 second blank wait into visible, word-by-word output. Implementation:

- **Backend**: `AsyncAnthropic` client with `client.messages.stream()` context manager; `stream.text_stream` is an async iterator of text tokens; `get_final_message()` collects the completed response for history and tool dispatch.
- **Frontend**: `fetch` + `ReadableStream` reader; SSE `data:` lines are parsed from the chunked body; tokens are appended to a live bubble element.

### 4. Nearby airport recommendations

`resolve_airport` previously returned `NOT_FOUND` for any city without a direct airport entry. It now has a three-tier resolution:

1. **Exact or partial match** → `FOUND` (direct airport)
2. **Known city without airport** → `NEARBY` (haversine distances to the 3 closest served airports)
3. **Unknown city** → `NOT_FOUND`

The haversine formula computes great-circle distances between the requested city's coordinates and every airport in the served network. Over 120 cities-without-airports are mapped (covering major suburbs and satellite cities across North America, Europe, and Asia-Pacific).

The partial-match fallback was also tightened to skip 3-character IATA codes as substrings, preventing spurious matches like "san" → "santa barbara".

### 5. Tightened system prompt

The system prompt was rewritten with explicit anti-hallucination rules enforced before any other instructions:

| Rule | What it prevents |
|---|---|
| Never guess an airport code | Inventing IATA codes from training data |
| Quote flight details verbatim | Rounding prices, misremembering times |
| Copy confirmation number character-for-character | Fabricating or recycling confirmation numbers |
| Require explicit verbal confirmation before booking | Booking on ambiguous phrases like "that sounds good" |
| Never reuse details from a previous booking | Cross-contamination in multi-booking calls |
| Only answer policy questions from the knowledge base | Inventing fees, timelines, or policies |

Additional structural changes: Step 6 (confirm) now includes a mandatory fill-in-the-blank script so the agent can't skip fields; the tool response reference is a lookup table instead of prose; the knowledge base includes a named fallback number (`1-800-SKY-LINE`) so the agent never has to decide what "I don't know" looks like.

---

## Setup

### 1 — Install dependencies

```bash
cd airline-voice-assistant
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2 — Configure environment variables

```bash
cp .env.example .env
```

Fill in `.env`:

| Variable | Required | Where to find it |
|---|---|---|
| `ANTHROPIC_API_KEY` | Yes | console.anthropic.com → API Keys |
| `TWILIO_ACCOUNT_SID` | For SMS | Twilio Console → Account Info |
| `TWILIO_AUTH_TOKEN` | For SMS | Twilio Console → Account Info |
| `TWILIO_PHONE_NUMBER` | For SMS | Twilio Console → Phone Numbers |
| `SENDGRID_API_KEY` | For email | SendGrid → Settings → API Keys |
| `SENDGRID_FROM_EMAIL` | For email | Any verified SendGrid sender |
| `TRANSFER_PHONE_NUMBER` | For Phonely | Your customer support line |
| `PORT` | No | Defaults to 8000 |

Only `ANTHROPIC_API_KEY` is required to run the agent. Twilio and SendGrid are only needed for the notification step; the rest of the booking flow works without them.

---

## Running the Agent

Always use the virtual environment Python:

```bash
source venv/bin/activate
python main.py
```

The server starts on `http://localhost:8000`.

| URL | What you get |
|---|---|
| `http://localhost:8000/agent` | Streaming chat UI (AI agent) |
| `http://localhost:8000/` | Step-by-step booking UI (direct tool calls) |
| `http://localhost:8000/health` | Health check |

---

## Phonely Voice Integration

### Step 1 — Expose the server

```bash
ngrok http 8000
```

Copy the `https://xxxx.ngrok.io` URL.

### Step 2 — Create a Phonely agent

Go to your Phonely dashboard → **Agents** → **Create Agent**.

### Step 3 — Set the system prompt

Paste the contents of `phonely/system_prompt.md` into the **System Prompt** field.

### Step 4 — Add tools

In Phonely **Actions**, add each tool from `phonely/tools_config.json`. For each:
- **Name / Description / Parameters**: copy from the JSON exactly
- **Webhook URL**: `https://your-ngrok-url/tools`

All four tools point to the same endpoint.

### Step 5 — Upload the knowledge base

Paste `phonely/knowledge_base.md` into the Phonely **Knowledge Base** section.

### Step 6 — Configure call transfer

Set the transfer destination to your support line. The system prompt already instructs the agent when to trigger it.

### Step 7 — Test calls

| Phrase | What it tests |
|---|---|
| "I want to fly from Los Angeles to New York on July 15th" | Full happy path |
| "I want to fly from Beverly Hills to Miami" | Nearby airport suggestion |
| "Fly from Aalborg to Vancouver" | No-flights error path |
| "I want to speak to an agent" | Human escalation |
| "What's your cancellation policy?" | Knowledge base |

---

## API Reference

### `POST /chat`

Streams the AI agent response as Server-Sent Events.

**Request body:**
```json
{"session_id": "abc-123", "message": "I want to fly from LA to New York"}
```

**Response** (`text/event-stream`):
```
data: {"t": "Sure"}\n\n
data: {"t": ", let"}\n\n
...
data: [DONE]\n\n
```

On error: `data: {"error": "message"}` before `[DONE]`.

### `POST /chat/reset`

Clears the conversation history for a session.

```bash
curl -X POST "http://localhost:8000/chat/reset?session_id=abc-123"
```

### `POST /tools`

Phonely webhook — executes a single tool and returns the result.

**Request body:**
```json
{
  "name": "check_flights",
  "parameters": {
    "origin_iata": "LAX",
    "destination_iata": "JFK",
    "travel_date": "2026-07-15"
  }
}
```

**Response:**
```json
{"result": "Available flights from LAX to JFK on 2026-07-15:\nOption 1: ..."}
```

### `GET /health`

```json
{"status": "ok", "service": "SkyLine Airways Voice Assistant"}
```

---

## Testing

### Chat agent (curl)

```bash
# Start a session
curl -sN -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test-1", "message": "Hello"}'

# Continue the same session
curl -sN -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test-1", "message": "I want to fly from Beverly Hills to New York on August 10th 2026"}'

# Reset
curl -X POST "http://localhost:8000/chat/reset?session_id=test-1"
```

### Individual tools (curl)

```bash
# Airport — direct match
curl -s -X POST http://localhost:8000/tools \
  -H "Content-Type: application/json" \
  -d '{"name": "resolve_airport", "parameters": {"city_name": "Los Angeles"}}'

# Airport — nearby suggestion
curl -s -X POST http://localhost:8000/tools \
  -H "Content-Type: application/json" \
  -d '{"name": "resolve_airport", "parameters": {"city_name": "Beverly Hills"}}'

# Flights — valid route
curl -s -X POST http://localhost:8000/tools \
  -H "Content-Type: application/json" \
  -d '{"name": "check_flights", "parameters": {"origin_iata": "LAX", "destination_iata": "JFK", "travel_date": "2026-08-01"}}'

# Flights — no-flights test case
curl -s -X POST http://localhost:8000/tools \
  -H "Content-Type: application/json" \
  -d '{"name": "check_flights", "parameters": {"origin_iata": "AAL", "destination_iata": "YVR", "travel_date": "2026-08-01"}}'

# Book
curl -s -X POST http://localhost:8000/tools \
  -H "Content-Type: application/json" \
  -d '{"name": "book_flight", "parameters": {"flight_id": "SKY101", "travel_date": "2026-08-01", "passenger_name": "Jane Smith", "contact_info": "jane@example.com"}}'
```
