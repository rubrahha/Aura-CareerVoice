# GitHub research and actual integration

## What was downloaded and reused?

The code components were **retrieved using the connected GitHub API** and adapted into this standalone project. The original full repositories are **not included or required**.

### 1. Aayushyaash/Rag-chatbot (MIT)
- Repository: https://github.com/Aayushyaash/Rag-chatbot
- Upstream source inspected: [`backend/retrieval/hybrid_retriever.py`](https://github.com/Aayushyaash/Rag-chatbot/blob/main/backend/retrieval/hybrid_retriever.py) and `keyword_retriever.py`.
- **Reused and modified:** reciprocal rank fusion combining independent retrieval result lists, in `app/integrations/rrf.py`.
- **Added locally:** zero-dependency BM25 index in `app/bm25.py`; merged with our preexisting TF-IDF vector retriever in `app/rag.py`.
- **Avoided:** ChromaDB, PDF model downloads, paid embeddings, and a second Flask frontend, because the assignment needs a fast, simple hosted career counselor.
- Original copyright (c) 2025 Aayush Yash; MIT notice below in THIRD_PARTY_NOTICES.md.

### 2. lythelab/voice-agent-starter-kit (MIT)
- Repository: https://github.com/lythelab/voice-agent-starter-kit
- Upstream source inspected: [`app/telemetry.py`](https://github.com/lythelab/voice-agent-starter-kit/blob/main/app/telemetry.py), `app/pipeline/conversation.py`, README.
- **Reused and modified:** in-memory latency measurement class at `app/integrations/telemetry.py`.
- **Integrated:** timing of real RAG retrieval and total backend generation; query `/api/latency/summary`.
- **Avoided:** its paid-provider speech configuration. Aura keeps browser microphone recognition + speech synthesis at no API service cost.
- Original copyright (c) 2026 lythe labs; MIT notice below in THIRD_PARTY_NOTICES.md.

## Actual voice → RAG → answer → speech workflow

1. Browser `SpeechRecognition` / `webkitSpeechRecognition` obtains text from microphone (or user types).
2. FastAPI accepts a question, past conversation and optional profile.
3. TF-IDF and BM25 each retrieve career documents from 40 local profiles; MIT-adapted RRF merges their ranked lists.
4. Gemini streaming API (if a valid free-tier key is configured) answers using that retrieved context. Otherwise, clearly labeled **rule-based demo**, not an LLM.
5. The browser streams text on screen and reads sentence chunks aloud with `speechSynthesis`.
6. Anonymous backend latency samples are available from `/api/latency/summary`.

**Scope:** The browser sends recognized text, not raw microphone audio, to FastAPI. Browser speech recognition can depend on a vendor service and is not guaranteed to be fully offline. Latency stats are backend only, and exclude speech recognition and client speech playback.

## How to test

```powershell
powershell -ExecutionPolicy Bypass -File .\start-windows.ps1
```

Then open `http://127.0.0.1:8000`, type a career question, check source details, ask a follow-up, enable audio, and visit `http://127.0.0.1:8000/api/latency/summary`.

Run 24 included automated tests with:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
```

**Known verification limits:** Local backend and JavaScript syntax are tested. End-to-end recognition and audible speaker playback require testing in your own Chrome/Edge browser. Gemini integration requires a real valid API key and is not verified against a live external AI account in this package. Public hosting remains to be performed in your Render account.

## License and attribution

Read `THIRD_PARTY_NOTICES.md` before publishing or distributing this code. Follow both MIT permissions and required notice retention.

## Final integration: actual upstream rolling conversation code

Selected repository: **[lythelab/voice-agent-starter-kit](https://github.com/lythelab/voice-agent-starter-kit)** (MIT). The upstream `app/pipeline/conversation.py` implementation was brought into the project as [`app/integrations/conversation.py`](app/integrations/conversation.py), with the original role-based message methods and history trimming retained. The constructor is adapted to accept prompt strings instead of relying on upstream app settings. The implementation is actively used inside `app/counselor.py::build_prompt`, which reconstructs the latest user/assistant turns before the Gemini call. This is not simply code stored unused.

Latency tracking previously adapted from the **same repository** is still active, and now includes time-to-first-token. Hybrid RAG ranking remains adapted from the other MIT repository, Aayushyaash/Rag-chatbot. Full original license notices are in `THIRD_PARTY_NOTICES.md`.

**Final verification:** 24 backend/regression automated tests passed including a mocked live LLM streaming response and server-side memory class integration. Browser UI interacted successfully against mocked API calls in Chromium at 1440px and 390px viewport widths, and a simulated microphone transcript triggered a question. These checks do not establish real audio hardware, third-party LLM availability, or public hosting.

## v3 — simple conversation UI

The previous dashboard-style UI was replaced with a minimal chat interface. It retains all core features and adds smoother progressive rendering, safe Markdown-like text formatting, Stop/Cancel, Copy, Read aloud, inline RAG sources, mobile navigation and session-scoped refresh recovery. The retained voice-agent memory, telemetry and RAG components are still active; the UI changes do not alter the MIT license obligations.

Browser testing uses headless Chromium with simulated HTTP/SSE and simulated microphone transcripts because the sandbox browser blocks connections to localhost. **Actual microphone hardware, Gemini API calls, and deployment must be tested separately**.
