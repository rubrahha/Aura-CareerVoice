# Publish Aura CareerVoice — GitHub + Render Free

This is a **real Python backend**, so GitHub Pages cannot host the live AI server. Use GitHub as source code hosting and Render for the public HTTPS app.

## Before you start
- Windows PowerShell and a working `git` command.
- Install official GitHub CLI if `gh` is missing: `winget install --id GitHub.cli -e` then reopen PowerShell.
- Authenticate once: `gh auth login --web` and select GitHub.com / HTTPS.
- **Do not upload `.env`, Gemini keys, or `.venv`.** This project's `.gitignore` excludes them.

## 1. Create the repository and push code

In the **root of this extracted project**, run:

```powershell
powershell -ExecutionPolicy Bypass -File .\publish-github.ps1
```

The script refuses to change an existing `.git` repository or to overwrite a preexisting repository. It requires account `rubrahha` and creates `https://github.com/rubrahha/Aura-CareerVoice-MinuteHire` when the name is available. To choose another name:

```powershell
powershell -ExecutionPolicy Bypass -File .\publish-github.ps1 -RepoName 'Aura-CareerVoice-Assessment'
```

Alternatively create an **empty** GitHub repository yourself, then `git init`, `git add .`, `git commit`, add the new remote and push. Never use an unrelated existing GitHub repository.

## 2. Deploy free on Render

1. Go to https://dashboard.render.com/ and sign in. Authorize your GitHub account if requested.
2. Choose **New → Blueprint**, select the new `Aura-CareerVoice-MinuteHire` repo, and use `render.yaml` in the root.
3. Verify the service plan says **Free**. If Free isn't available, **do not confirm a paid plan**.
4. At the secret prompt / environment settings, set **`GEMINI_API_KEY`** to a valid Google AI Studio API key. Never paste it into source code or GitHub. If you skip the key, the site works only in clearly labelled **demo** mode and is not the complete assignment.
5. Start deployment. Render assigns a live URL such as `https://<chosen-service>.onrender.com`; **do not guess the URL** — copy it from your Render dashboard.
6. Run the smoke check after Render reports the deploy as live:

```powershell
powershell -ExecutionPolicy Bypass -File .\verify-live.ps1 -Url 'https://YOUR-ACTUAL-SERVICE.onrender.com'
```

## 3. Verify before MinuteHire submission

- Open the live page in Chrome or Edge, allow microphone, ask an education/career question aloud.
- Check the recognized transcript, real Gemini voice answer, and audio playback; verify mode from `/api/health` is `gemini` (configuration check only).
- Ask a related follow-up; check memory and source references.
- Open an incognito window and confirm the URL works for a visitor.
- Check that API errors and fallback mode are *visible* and do not masquerade as LLM responses.

**Caution:** Browser-based voice recognition depends on the browser/platform; it is not a dedicated streaming speech provider. Render Free services sleep after inactivity and may take around a minute to wake. Any free AI API has rate quotas; free availability can change.

**Deployment status:** This code is prepared for publishing, but neither GitHub repository creation nor public Render deployment occurs automatically by downloading this ZIP.

Official documentation: https://render.com/docs/deploy-fastapi ; https://render.com/docs/blueprint-spec ; https://render.com/docs/free
