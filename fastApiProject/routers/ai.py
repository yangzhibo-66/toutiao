import os
import json
from typing import Any

import httpx
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/api/ai", tags=["ai"])

DASHSCOPE_API_ENDPOINT = os.getenv(
    "DASHSCOPE_API_ENDPOINT",
    "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
).strip()
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "").strip()
DASHSCOPE_MODEL = os.getenv("DASHSCOPE_MODEL", "qwen-max").strip()
AI_TIMEOUT_SECONDS = float(os.getenv("AI_CHAT_TIMEOUT_SECONDS", "90"))


def _build_payload(payload: dict[str, Any]) -> dict[str, Any]:
    messages = payload.get("messages")
    if not isinstance(messages, list) or not messages:
        raise HTTPException(status_code=400, detail="messages is required")

    return {
        "model": payload.get("model") or DASHSCOPE_MODEL,
        "messages": messages,
        "stream": payload.get("stream", True),
    }


@router.post("/chat")
async def chat(request: Request):
    if not DASHSCOPE_API_KEY:
        raise HTTPException(status_code=500, detail="AI service is not configured")

    payload = _build_payload(await request.json())
    headers = {
        "Authorization": f"Bearer {DASHSCOPE_API_KEY}",
        "Content-Type": "application/json",
        "X-DashScope-SSE": "enable",
    }

    async def stream_response():
        timeout = httpx.Timeout(AI_TIMEOUT_SECONDS, connect=20)
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                async with client.stream(
                    "POST",
                    DASHSCOPE_API_ENDPOINT,
                    headers=headers,
                    json=payload,
                ) as response:
                    if response.status_code >= 400:
                        error_text = await response.aread()
                        detail = error_text.decode("utf-8", errors="ignore") or "AI request failed"
                        error_payload = {
                            "error": {
                                "message": f"AI request failed: HTTP {response.status_code} {detail}"
                            }
                        }
                        yield f"data: {json.dumps(error_payload, ensure_ascii=False)}\n\n".encode("utf-8")
                        yield b"data: [DONE]\n\n"
                        return
                    async for chunk in response.aiter_bytes():
                        yield chunk
        except Exception as exc:
            error_payload = {"error": {"message": f"AI proxy failed: {exc}"}}
            yield f"data: {json.dumps(error_payload, ensure_ascii=False)}\n\n".encode("utf-8")
            yield b"data: [DONE]\n\n"

    return StreamingResponse(stream_response(), media_type="text/event-stream")
