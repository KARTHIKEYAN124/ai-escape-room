# AI Escape Room — The Midnight Library

A Python escape-room game with a Streamlit chat interface and Google Gemini integration. Explore a locked library, collect clues, solve three connected puzzles and unlock the exit.

## Run the app

Install Python and Git. The project was tested with Python 3.14.

### Windows PowerShell

```powershell
git clone https://github.com/KARTHIKEYAN124/ai-escape-room.git
cd ai-escape-room
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python -m streamlit run app.py
```

### macOS / Linux

```bash
git clone https://github.com/KARTHIKEYAN124/ai-escape-room.git
cd ai-escape-room
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m streamlit run app.py
```

Open the localhost URL printed in the terminal, usually `http://localhost:8501`. Access to this private repository is required to clone it.

## Configure Gemini

1. Get a Gemini API key from [Google AI Studio](https://aistudio.google.com/apikey).
2. In the sidebar, choose a version and select **Gemini API** under **Game Master**.
3. Paste the raw key into **Gemini API key**, without quotes or `GEMINI_API_KEY=`.
4. Click **Load available models** and choose a compatible Gemini text model.
5. Send `examine the desk` in the chat box.

Alternatively, set `GEMINI_API_KEY` and `GEMINI_MODEL` in the process environment before launching. The app does not automatically read `.env` files. Keys entered through the sidebar are not written to disk. Never commit a real key.

Select **Offline demo** to play without credentials or API requests. Use a Google project with eligible free-tier access and no paid billing enabled if zero cost is required. Available models and quotas depend on your project; listing a model does not guarantee free access.

## Versions

| Version | Behavior with Gemini API |
|---|---|
| **Version 1 · Interactive** | Gemini manages narration and progress through conversation, reporting escape with a completion marker. Rules are prompt instructions. |
| **Version 2 · Reliable** | Gemini interprets the action; Python validates inventory, combinations and prerequisites using structured state. Narration is restricted to approved outcomes. |

Both version selections use the same validated Python engine in **Offline demo**. Choose **Gemini API** to experience their differences. Version 2 shows a warning when an API failure causes offline fallback.

## Play

Investigate the desk, bookshelf, painting, drawer and door. Send one action per message:

```text
examine the desk
examine the bookshelf
examine the drawer
inventory
hint
```

Other action forms include `enter 123 on the drawer`, `take the key`, `use the key on the painting` and `enter 1234 on the door`. The example numbers are placeholders; discover the actual combinations from the clues.

Version 2 displays inventory and puzzle progress. Use **Restart game** to start again. Changing version or mode also resets the game. Conversation and progress are stored per browser session, without permanent saved games.

## Troubleshooting

| Problem | Action |
|---|---|
| Invalid key / 401 / 403 | Check the sidebar key and Google project restrictions. |
| Model not found / 404 | Reload available models and select a compatible Gemini text model. Version 1 also attempts one discovered Flash replacement. |
| Rejected request / 400 | Check the selected model and project eligibility. Antigravity agents require a different API. |
| Quota / 429 | Check project limits and retry after reset; a new key in the same project does not reset quota. |
| Temporary server error / 500, 502, 503, 504 | The app retries once. If it still fails, wait and resend the action. Previous Version 1 conversation is preserved. |
| Offline command not recognized | Name the target object, use one action per message, or type `hint`. |

## Repository files

```text
app.py             Streamlit interface, chat and session handling
game.py            Structured state, inventory, puzzles and action validation
llm.py             Gemini integration, narration and request recovery
requirements.txt   Runtime dependencies
README.md          Setup and usage instructions
.gitignore         Excludes credentials and non-runtime local files
```
