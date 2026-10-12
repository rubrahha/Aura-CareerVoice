# MinuteHire AI Engineer Assessment — submission guide

**App name:** Aura — AI Voice Career Counselor

**Live app URL:** `PASTE_YOUR_DEPLOYED_HTTPS_URL_HERE` (must replace with a real working link)

**Candidate demo script (90 seconds):**

1. Open your Render link in Chrome/Edge, allow microphone access, and ensure it displays **Gemini AI** (Gemini key configured).
2. Say: "I'm a BCA student. I like design but not heavy coding. What careers could fit?"
3. Hear the voice response and show the live transcript.
4. Ask: "What skills would I need for the second option?" Confirm that the app recalls prior conversation.
5. Click **career references** to show retrieved RAG source titles and cosine similarity scores.
6. Open **Career library**, search "security" or "AI", and test a second career.
7. Explain the latency measured by the app (retrieval milliseconds and total response duration).

**One-minute technical explanation:**

"I built Aura with Python/FastAPI and a no-build responsive web client. Browser speech recognition converts speech to text, and locally hosted TF-IDF + BM25 + RRF vectors retrieve the most relevant of 40 curated career entries by cosine similarity. I pass the retrieved evidence, profile details, and recent dialogue to the Gemini API, returning tokens via a streamed SSE endpoint. Browser speech synthesis speaks completed sentences as tokens arrive. The fallback demo mode works without a key but is transparently marked as non-LLM. This is a low-cost architecture that avoids paid STT/TTS and vector-database services. For production I would improve multilingual semantic retrieval, browser speech coverage, observability, rate limiting, reliability and testing." 

**Checklist before sharing with interviewer:**

- [ ] Live HTTPS URL is accessible without login.
- [ ] Status reads **Gemini AI**, not only **Knowledge demo**.
- [ ] Microphone permissions accepted; test browser support.
- [ ] Student can speak and hear an AI answer.
- [ ] Follow-up questions preserve context.
- [ ] Source cards show actual retrieved documents.
- [ ] Gemini key remains in hosted environment variables, never GitHub.
- [ ] Give the first request time to wake if hosted on a sleeping free instance.

**Known tradeoffs:** Browser speech can depend on online vendor services, free hosting has cold starts, RAG uses lexical TF-IDF + BM25 + RRF instead of dense embeddings, and there is no user authentication or durable sessions. No claim of production-grade real-time latency is made.
