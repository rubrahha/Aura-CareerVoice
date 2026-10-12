# Create the free public URL required by MinuteHire

## A. Run locally (Windows 10/11; PowerShell)

1. Extract `Aura_CareerVoice_Deploy_Ready.zip` into any folder, e.g. `E:\Aura_CareerVoice`.
2. Open **PowerShell** in that folder and run:

```powershell
powershell -ExecutionPolicy Bypass -File .\start-windows.ps1
```

3. Open `http://127.0.0.1:8000` in **Chrome or Edge**. Typing works with no API key; the offline demo is **not** a replacement for the assessment's LLM requirement.
4. Obtain a Gemini key from `https://aistudio.google.com/apikey` (free API access is subject to limits and eligibility). Open `.env` and set:

```dotenv
GEMINI_API_KEY=PASTE_YOUR_KEY_HERE
AI_MODE=auto
GEMINI_MODEL=gemini-2.5-flash-lite
```

5. Stop/restart the PowerShell server. Check `http://127.0.0.1:8000/api/health` says `"mode": "gemini"`. **This checks configuration only**: send an actual question to verify provider access. If the model is unavailable to your key, select a supported free-tier model in Google AI Studio and update `GEMINI_MODEL`.

## B. Push the project to GitHub

In a new terminal in the project folder:

```powershell
git init
git add .
git commit -m "Build MIT-attributed RAG voice career counselor for MinuteHire"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_NEW_REPOSITORY.git
git push -u origin main
```

Create **an empty repository** on GitHub before the `git remote add` step. `.env` and `.venv` are excluded by `.gitignore`; do not commit secrets or private student data. If git prompts for authentication, sign in using your chosen GitHub authentication method.

## C. Deploy on Render

1. Visit `https://dashboard.render.com/` and sign in.
2. **New > Blueprint**: connect the new GitHub repository. This project's `render.yaml` defines a Python web service. Confirm that the selected plan is **Free**, if offered in your account/region.
3. In Render environment settings, set `GEMINI_API_KEY` as a secret. Don't add it to GitHub. `GEMINI_MODEL` defaults to `gemini-2.5-flash-lite`.
4. Wait for deploy, then visit the **actual URL** that Render assigns to you, usually `https://<service-name>.onrender.com/`.
5. Accept the microphone permission in Chrome/Edge, check that speech is recognized and spoken response plays. Check a follow-up question and source references.
6. Test incognito access. Send this **real** link as the MinuteHire submission.

**Important:** Free web servers can sleep and have cold-start delays. Google free-tier models and quotas are not guaranteed forever. Render and other vendors set their own conditions; check their current plans before enabling billing.

## D. Run tests

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
```

The included automated tests validate backend retrieval, prompt memory, stream formatting, fallback handling, and a **mocked** Gemini stream. Actual provider/audio/live-host integration needs the manual checks above.
