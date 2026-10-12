"""One-service deployment for UI, vector retrieval, and LLM voice-counselor API."""
import asyncio
from collections import defaultdict, deque
from contextlib import asynccontextmanager
import json
import os
import httpx
from pathlib import Path
import time

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .counselor import build_prompt, configured_mode, demo_response, demo_stream, gemini_stream
from .rag import get_index, public_sources, retrieve
from .integrations.telemetry import latency_store
from .schemas import ChatRequest

load_dotenv(Path(__file__).resolve().parent.parent / ".env")
BASE = Path(__file__).parent
WINDOW = 60
request_history: dict[str, deque] = defaultdict(deque)


@asynccontextmanager
async def lifespan(app: FastAPI):
    get_index()   # warm index before first incoming request
    yield


app = FastAPI(title="MinuteHire CareerVoice API", version="1.0.0", lifespan=lifespan,
              description="Voice career counselor with local TF-IDF RAG and optional Gemini LLM.")
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")


def check_rate_limit(request: Request):
    # In-memory limit is per instance, best-effort and not a production-grade abuse defense.
    ip = request.client.host if request.client else "unknown"
    # Prefer direct socket IP; proxy forwarding requires a trusted proxy configuration.
    times = request_history[ip]
    now = time.monotonic()
    while times and now - times[0] > WINDOW:
        times.popleft()
    limit = min(max(int(os.getenv("REQUESTS_PER_MINUTE", "25")), 1), 120)
    if len(times) >= limit:
        raise HTTPException(429, "Too many requests. Please try again in a minute.")
    times.append(now)


@app.get("/", include_in_schema=False)
async def home():
    return FileResponse(BASE / "static" / "index.html")


@app.get("/api/health")
async def health():
    index = get_index()
    return {"status": "ok", "mode": configured_mode(), "knowledge_entries": len(index.careers),
            "retrieval": "TF-IDF + BM25 + RRF (MIT-adapted)",
            "model": os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite") if configured_mode() == "gemini" else None,
            "voice": "browser-native"}


@app.get("/api/latency/summary")
async def latency_summary():
    """Anonymous aggregate timings inspired by MIT voice-agent-starter-kit."""
    return {"metrics": latency_store.summary(), "units": "milliseconds",
            "storage": "in-memory, most recent 300 samples per metric"}


@app.get("/api/topics")
async def topics():
    return [{"id": x["id"], "title": x["title"], "cluster": x["cluster"]}
            for x in get_index().careers]


@app.post("/api/chat")
async def chat(body: ChatRequest, request: Request):
    """JSON API for tests/integrations. The browser uses streaming below."""
    check_rate_limit(request)
    started = time.perf_counter()
    docs, retrieval_ms = retrieve(body.message, body.history, body.profile)
    latency_store.add("rag_retrieval_ms", retrieval_ms)
    mode = configured_mode()
    fallback_notice = None
    if mode == "gemini":
        parts = []
        try:
            async for part in gemini_stream(build_prompt(body.message, body.history, body.profile, docs)):
                parts.append(part)
            answer = "".join(parts).strip()
            if not answer:
                raise RuntimeError("AI provider returned no text.")
        except Exception as exc:
            mode = "fallback"
            fallback_notice = str(exc) if isinstance(exc, RuntimeError) else "AI service timed out or disconnected."
            answer = demo_response(body.message, body.history, body.profile, docs)
    else:
        answer = demo_response(body.message, body.history, body.profile, docs)
    latency_store.add("total_response_ms", (time.perf_counter() - started) * 1000)
    return {"answer": answer, "mode": mode, "notice": fallback_notice,
            "sources": public_sources(docs), "retrieval_ms": retrieval_ms}


def sse(event: str, data: object) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@app.post("/api/chat/stream")
async def stream_chat(body: ChatRequest, request: Request):
    check_rate_limit(request)

    async def events():
        started = time.perf_counter()
        docs, retrieval_ms = retrieve(body.message, body.history, body.profile)
        latency_store.add("rag_retrieval_ms", retrieval_ms)
        mode = configured_mode()
        yield sse("sources", {"sources": public_sources(docs), "retrieval_ms": retrieval_ms})
        answer = ""
        notice = None
        first_token_ms = None

        def record_first_token():
            nonlocal first_token_ms
            if first_token_ms is None:
                first_token_ms = round((time.perf_counter() - started) * 1000, 1)
                latency_store.add("first_token_ms", first_token_ms)

        if mode == "gemini":
            try:
                async for delta in gemini_stream(build_prompt(body.message, body.history, body.profile, docs)):
                    answer += delta
                    record_first_token()
                    yield sse("delta", {"text": delta})
                if not answer.strip():
                    raise RuntimeError("AI provider returned an empty answer.")
            except Exception as exc:
                if answer.strip():
                    # A partial answer is safer than silently replacing the streamed transcript.
                    notice = "AI stream interrupted; partial response shown."
                else:
                    mode = "fallback"
                    notice = str(exc) if isinstance(exc, RuntimeError) else "AI service temporarily unavailable."
                    async for part in demo_stream(demo_response(body.message, body.history, body.profile, docs)):
                        answer += part
                        record_first_token()
                        yield sse("delta", {"text": part})
        else:
            async for delta in demo_stream(demo_response(body.message, body.history, body.profile, docs)):
                answer += delta
                record_first_token()
                yield sse("delta", {"text": delta})
        total_ms = round((time.perf_counter() - started) * 1000, 1)
        latency_store.add("total_response_ms", total_ms)
        yield sse("done", {"mode": mode, "notice": notice, "answer": answer,
                           "total_ms": total_ms, "first_token_ms": first_token_ms})

    return StreamingResponse(events(), media_type="text/event-stream", headers={
        "Cache-Control": "no-cache, no-transform", "X-Accel-Buffering": "no", "Connection": "keep-alive"})
