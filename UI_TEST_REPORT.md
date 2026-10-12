# Aura v3 — UI and test report

## UI changes
- Replaced dashboard styling with plain, readable, ChatGPT-inspired conversation UI.
- One message input, microphone button, speaker toggle, and Stop button; New chat and optional settings.
- Streamed text renders progressively and is displayed as paragraphs, bold labels, headings and lists.
- Responses offer Copy, Read aloud, and the actual named RAG career sources.
- Follow-up context persists in browser session storage; the backend remains stateless.
- Simple mobile menu, responsive layout, keyboard access and no third-party front-end dependencies.

## Executed checks
1. `python -m pytest -q` — **24 passed**.
2. `node --check app/static/app.js` — JavaScript syntax clean.
3. `python scripts/browser_smoke_mock.py` — **desktop and mobile checks passed** with the actual browser JS and mocked API responses obtained from FastAPI. Checks included progressive SSE parsing, Markdown formatting, sources, new chat, typed input, simulated mic transcript, Stop, profile and responsive overflow.
4. FastAPI local response was checked through test client; screenshots under `previews/`.

## Still needs device / account verification
- Real microphone permissions and speech-recognition service in Chrome or Edge.
- Actual audible speaker/TTS on your computer.
- Real Gemini API responses using your key (the tests simulate these, do not use real credentials).
- Public HTTPS deployment and mobile browser test on the final live URL.

The no-key version uses a **rule-based knowledge demo**, not an LLM. Do not submit that as a live LLM assessment.
