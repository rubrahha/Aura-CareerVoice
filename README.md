# Aura CareerVoice

**AI Voice Career Counselor — MinuteHire AI Engineer Assessment**

🌐 **[Open the live app](https://auracareervoicedeployready.vercel.app/)**

Aura is a simple ChatGPT-style career counselor. Students can type or speak questions about jobs, skills, courses and career choices. Aura searches its own career knowledge base and replies in readable, gradually appearing text. Compatible browsers can also read answers aloud.

> **Current live status:** The provided Vercel URL loads, and `/api/health` reports **demo mode** with 40 career entries. Real Gemini-generated responses require a server-side `GEMINI_API_KEY`. Browser voice must be tested on a real device.

## How it works (simple)

1. **Ask:** A student asks by typing or microphone.
2. **Convert:** The browser turns speech into text, when supported.
3. **Find:** RAG searches 40 saved career profiles using TF-IDF + BM25 + rank fusion.
4. **Answer:** Gemini writes the answer when configured; otherwise the application uses its knowledge-based demo.
5. **Reply:** Text streams into the chat and the browser can speak it aloud.
6. **Remember:** Recent chat turns help answer follow-up questions.

## Project folders

```text
Aura-CareerVoice/
├── app/                         # Main Python application
│   ├── main.py                  # FastAPI routes and streaming
│   ├── counselor.py             # Gemini model + demo responses
│   ├── rag.py                   # Finds useful career information
│   ├── bm25.py                  # Keyword search
│   ├── schemas.py               # Validates requests
│   ├── integrations/            # Chat memory, rank fusion, speed tracking
│   ├── data/
│   │   ├── careers.json         # 40 career guides used for RAG
│   │   └── make_careers.py      # Career data maintenance script
│   └── static/
│       ├── index.html           # Chat page
│       ├── styles.css           # Minimal layout
│       ├── app.js               # Chat, streaming and microphone
│       └── favicon.svg          # App icon
├── tests/                       # Automated tests
├── scripts/                     # Optional browser smoke test
├── .env.example                 # Example environment configuration
├── requirements.txt             # Python dependencies
├── start-windows.ps1            # Run locally on Windows
├── start-linux.sh               # Run locally on Linux
├── render.yaml                  # Optional hosting configuration
└── README.md                    # This guide
```

## Run it locally (Windows)

Install **Python 3.12**, then open PowerShell inside the project folder:

```powershell
powershell -ExecutionPolicy Bypass -File .\start-windows.ps1
```

Open **http://127.0.0.1:8000** in Chrome or Edge.

No API key is required for the **demo**. To enable genuine AI-written answers, copy `.env.example` to `.env` and set `GEMINI_API_KEY` there. Never upload the `.env` file or your credentials to GitHub.

## Features

- ChatGPT-inspired simple chat interface
- Typed and spoken questions (browser dependent)
- Progressive, readable answers
- RAG over 40 career profiles
- Gemini integration (requires your key and quota)
- Recent conversation memory and follow-up questions
- Browser text-to-speech
- Sources, stop generation, copy answer, and new chat
- Backend latency measurements and automated tests

## Check whether the app is working

- [Live interface](https://auracareervoicedeployready.vercel.app/)
- [Health endpoint](https://auracareervoicedeployready.vercel.app/api/health)

**Note:** An accessible site and healthy backend do not alone prove live Gemini, voice hardware or real-time streaming have been tested. The project can run without an API key in **demo mode**.

## Open-source credits

Parts of RRF, latency reporting and conversation memory were adapted from MIT-licensed projects: [Aayushyaash/Rag-chatbot](https://github.com/Aayushyaash/Rag-chatbot) and [lythelab/voice-agent-starter-kit](https://github.com/lythelab/voice-agent-starter-kit). See `THIRD_PARTY_NOTICES.md` for license notices.

---

**Repository:** https://github.com/rubrahha/Aura-CareerVoice

**Live URL:** https://auracareervoicedeployready.vercel.app/
