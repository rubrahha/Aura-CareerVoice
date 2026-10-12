# MinuteHire assessment checklist — Aura CareerVoice

This is a **functional submission candidate**, not an already-submitted live website.
It implements the 4-page assignment's RAG voice career counselor requirements.
A **valid Gemini key and a public deployment** are still needed for the evaluator to test a live LLM.

| MinuteHire evaluation area | Implemented | How to demonstrate |
|---|---|---|
| RAG | Yes: local TF-IDF vectors + BM25 + MIT-adapted reciprocal rank fusion | Ask a career question, select an answer’s **sources** button, inspect ranked matching notes. No dense neural embedding model is claimed. |
| LLM | Gemini SSE response generation implemented; actual API credentials required | Set `GEMINI_API_KEY` in `.env` or Render and verify **Gemini AI**; mock-based integration test passed. |
| Voice | Browser speech-to-text + queued browser text-to-speech | Click microphone in supported Chrome/Edge on HTTPS or localhost; enable voice replies; allow mic permission. Physical audio not automated here. |
| Conversation | Recent 12 messages sent by the browser; adapted upstream `ConversationManager` trims and formats context | Ask about Data Analyst, then ask **"What skills should I learn for that?"** |
| Latency | Streaming SSE and sentence-level TTS; API timing stats including first token and retrieval | Request `/api/latency/summary`. These are server metrics; actual end-user latency depends on the network, browser, and LLM. |
| Prompt engineering | Counselor system prompt, career-grounded context, concision and honesty rules | Ask about career fit, education, skills and next steps. Verify no invented salary promises. |
| Knowledge base | 40 structured, locally curated career profiles | Open **Explore careers** and inspect `app/data/careers.json`. Not real-time labor market data. |
| Architecture | One FastAPI service hosting static UI, retrieval engine, streaming LLM integration and voice/browser bridge | Explain `app/main.py`, `app/rag.py`, `app/counselor.py`, `app/static/app.js`. |
| Deployment | `render.yaml` + Windows/Linux launchers + free-tier guide included | Push to your GitHub, deploy to a Python host/Render; **a live URL is not yet created**. |
| Problem solving | MIT license provenance, pytest regression tests, no-key fallback, input validation and simple privacy notes | `python -m pytest -q` and read `GITHUB_INTEGRATION.md`. |

## Required manual end-to-end checks before sending to MinuteHire

1. Create and configure a **valid Gemini API key** in your local `.env` (or hosting service's secret environment variables).
2. Start the app and verify `/api/health` shows `"mode":"gemini"`.
3. Ask the assignment's example prompt: **"I am a computer science student. I enjoy building products but I'm not very interested in hardcore coding. What career options could I explore?"**
4. Ask **"Which one has fewer coding tasks?"** then **"What skills should I learn first?"**. Confirm prior turns matter.
5. Click the microphone; allow access; confirm recognized speech, received answer, and audible spoken reply.
6. Check an answer’s **sources** button displays relevant named references.
7. Check `/api/latency/summary` for `rag_retrieval_ms`, `first_token_ms` and `total_response_ms`.
8. Deploy and open the **HTTPS URL** in an incognito browser to confirm evaluator access without sign-in. Warm an idle free host before any scheduled demo.
9. Send the **real** deployed URL (not a placeholder). The assessment explicitly requires an accessible URL.

## Honest limitations

- Without an API key, the interface runs a **clearly marked, rule-based knowledge demo**, not a live LLM.
- SpeechRecognition availability and network behavior depend on the browser and permission. Chrome/Edge are recommended, with typing as fallback.
- Free API quotas, model availability and hosting plans may change. There is no unlimited-cost guarantee.
- Knowledge base is curated for educational use. It is not a verified current job/salary database or professional licensing authority.
- 24 backend/regression tests and mocked browser interactions (desktop/mobile, simulated microphone, Stop) are verified. This package is **not** evidence of a successful external Gemini call, physical mic/TTS playback, or a completed public deployment.
