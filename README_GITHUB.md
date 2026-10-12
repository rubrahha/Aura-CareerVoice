# Aura CareerVoice — AI Voice Career Counselor

**Live website:** https://auracareervoicedeployready.vercel.app/

Aura is a simple ChatGPT-style **voice career counselor** developed for the **MinuteHire AI Engineer Assessment**. Students can ask questions by typing or speaking, get career suggestions, and ask follow-up questions. Its career knowledge base supports 40 career profiles.

> **Current live status (checked 12 October 2026):** the Vercel site loads and `/api/health` reports `status: ok`, `knowledge_entries: 40`, `mode: demo`. This is the free knowledge-based mode. **Live Gemini AI is not active**, so the LLM requirement is not yet fully demonstrated. Microphone/speech output have not been verified on a real device.

## How it works (simple explanation)

1. A student speaks or types a career question.
2. Browser speech recognition turns spoken words into text.
3. The Python backend searches the stored career information using RAG (TF-IDF + BM25 + RRF).
4. When a Gemini API key is configured, Gemini produces a personalized answer from the retrieved references; without a key, the app gives a simpler template-based demonstration answer.
5. The answer appears progressively, and the browser can read it aloud.
6. The next question can use the context of earlier messages.

## Features

- Simple chat interface for desktop and mobile
- Voice input and read-aloud responses using browser speech APIs
- Live text streaming, stop generating, copy response, and new chat
- Conversation memory across follow-up questions in the current session
- RAG over 40 curated career profiles, with source titles shown
- Optional Gemini LLM mode; free demo mode without a key
- API health check and latency measurements

## Folder structure

```text
Aura-CareerVoice/
├── app/                         Main Python application
│   ├── main.py                  FastAPI server, API routes and streaming
│   ├── counselor.py             Career response logic and Gemini integration
│   ├── rag.py                   Search relevant career information (RAG)
│   ├── bm25.py                  Keyword ranking used by RAG
│   ├── schemas.py               API request validation
│   ├── data/
│   │   ├── careers.json         Career knowledge base (40 profiles)
│   │   └── make_careers.py      Maintains the sample career data
│   ├── integrations/
│   │   ├── conversation.py      Remembers recent chat turns
│   │   ├── rrf.py               Combines retrieval results
│   │   └── telemetry.py         Measures response speed
│   └── static/
│       ├── index.html           Chat page
│       ├── styles.css           Clean UI design
│       ├── app.js               Chat, microphone, speech and streaming
│       └── favicon.svg          Website icon
├── tests/                       Automated backend tests
├── scripts/                     Optional browser test utility
├── .github/workflows/           GitHub Actions tests
├── .env.example                 Example configuration; NO real secrets
├── requirements.txt             Python libraries
├── render.yaml                  Render web deployment settings
├── start-windows.ps1            Start locally on Windows
├── start-linux.sh               Start locally on Linux
├── THIRD_PARTY_NOTICES.md       Open-source licenses and attribution
└── README.md                    This guide
```

## Run locally (Windows PowerShell)

Install Python 3.12, download or clone this repository, then in its root folder run:

```powershell
powershell -ExecutionPolicy Bypass -File .\start-windows.ps1
```

Open `http://127.0.0.1:8000` in Chrome or Edge. A local `.env` will be created if needed, and the **demo mode works without a key**.

To enable an actual Gemini LLM, copy `.env.example` to `.env`, put your real `GEMINI_API_KEY` in `.env` (or configure it as a hosting provider environment variable), and restart. **Never commit `.env`, keys, or `.venv` to GitHub.**

## Tests

```powershell
py -3.12 -m pip install -r requirements-dev.txt
py -3.12 -m pytest -q
```

The previously packaged version passed 24 local backend/regression tests; perform fresh tests after deployment and verify real voice input/output in a browser.

## Deployment

The provided live site is hosted on Vercel: https://auracareervoicedeployready.vercel.app/

The repo includes a `render.yaml` as an alternative Python hosting option. Configure `GEMINI_API_KEY` securely in your hosting dashboard to activate LLM answers. Confirm the active deployment points to the latest GitHub commit; a public URL being reachable does not by itself confirm that it redeployed this repository.

## Open-source credits

Selected MIT-licensed code has been adapted from [Voice Agent Starter Kit](https://github.com/lythelab/voice-agent-starter-kit) and [RAG Chatbot](https://github.com/Aayushyaash/Rag-chatbot). See `THIRD_PARTY_NOTICES.md` for license notices.

**Assessment reminder:** Live voice conversation, real Gemini responses, response speed, and a working accessible link should all be demonstrated before the MinuteHire submission.
