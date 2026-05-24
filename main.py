import json
import logging
import os
from pathlib import Path
from typing import Optional, Tuple
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse, StreamingResponse
from dotenv import load_dotenv
from pydantic import BaseModel

from tools.airport import resolve_airport
from tools.flights import check_flights
from tools.booking import book_flight
from tools.notifications import send_confirmation
import agent

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent

app = FastAPI(title="SkyLine Airways Voice Assistant API")

TOOL_HANDLERS = {
    "resolve_airport": resolve_airport,
    "check_flights": check_flights,
    "book_flight": book_flight,
    "send_confirmation": send_confirmation,
}


def _extract_tool_and_args(body: dict) -> Tuple[Optional[str], dict]:
    """
    Handle the different payload shapes Phonely may send.
    Phonely typically sends: {"name": "...", "parameters": {...}}
    Also handles OpenAI function-call style: {"function": {"name": "...", "arguments": "{...}"}}
    """
    # Shape 1: flat  {"name": "...", "parameters": {...}}
    if "name" in body:
        args = body.get("parameters") or body.get("arguments") or {}
        if isinstance(args, str):
            args = json.loads(args)
        return body["name"], args

    # Shape 2: nested  {"function": {"name": "...", "arguments": "{...}"}}
    if "function" in body:
        fn = body["function"]
        args = fn.get("arguments", {})
        if isinstance(args, str):
            args = json.loads(args)
        return fn.get("name"), args

    # Shape 3: tool_name key
    if "tool_name" in body:
        args = body.get("parameters") or body.get("arguments") or {}
        return body["tool_name"], args

    return None, {}


@app.post("/tools")
async def handle_tool_call(request: Request):
    body = await request.json()
    logger.info("Incoming tool call: %s", json.dumps(body))

    tool_name, parameters = _extract_tool_and_args(body)

    if not tool_name:
        raise HTTPException(status_code=400, detail="Could not parse tool name from request body.")

    if tool_name not in TOOL_HANDLERS:
        raise HTTPException(status_code=404, detail=f"Unknown tool: '{tool_name}'")

    try:
        result = TOOL_HANDLERS[tool_name](**parameters)
        logger.info("Tool '%s' result: %s", tool_name, result)
        return JSONResponse({"result": result})
    except TypeError as e:
        logger.error("Bad parameters for '%s': %s", tool_name, e)
        return JSONResponse({"error": f"Invalid parameters: {e}"}, status_code=400)
    except Exception as e:
        logger.error("Tool '%s' raised: %s", tool_name, e)
        return JSONResponse({"error": str(e)}, status_code=500)


class ChatRequest(BaseModel):
    session_id: str
    message: str


@app.post("/chat")
async def chat_endpoint(req: ChatRequest):
    async def generate():
        try:
            async for token in agent.chat_stream(req.session_id, req.message):
                yield f"data: {json.dumps({'t': token})}\n\n"
        except Exception as e:
            logger.error("Agent stream error: %s", e)
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.post("/chat/reset")
async def reset_chat(session_id: str):
    agent.reset_session(session_id)
    return {"status": "reset"}


@app.get("/agent", response_class=HTMLResponse)
async def serve_agent_ui():
    with open(BASE_DIR / "static" / "agent.html", "r") as f:
        return HTMLResponse(content=f.read())


@app.get("/", response_class=HTMLResponse)
async def serve_ui():
    with open(BASE_DIR / "static" / "index.html", "r") as f:
        return HTMLResponse(content=f.read())


@app.get("/health")
async def health():
    return {"status": "ok", "service": "SkyLine Airways Voice Assistant"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)), reload=True)
