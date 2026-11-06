# Submission checklist

| Requirement | Delivered artifact | Verification |
|---|---|---|
| 1. Working interactive Version 1 | `app.py` Version 1 selector; `llm.py` Game Master, conversation, escape marker, error recovery | Mocked AI chat completion, model recovery and failure-preservation tests; user-provided live narration excerpts |
| 2. Reliable Version 2 | `game.py` structured State, inventory and action validation; `llm.py` action interpretation and constrained outcome selection | Full escape, invalid actions, prerequisite checks, secret protection and repeated-action tests |
| 3. Architecture for each version | `architecture-v1.svg`, `architecture-v2.svg`, editable Mermaid in `architecture.md` | SVG is standalone and opens in a browser without Mermaid tooling |
| 4. At least five comparative cases | Seven executed cases in `comparison-results.md` and `.json`; protocol in `test-cases.md` | Fault injection at actual model boundary; all seven Version 2 state-integrity checks pass |
| 5. Short report, 2-3 pages | `report.pdf` (exactly 3 A4 pages), editable `report.md` | PDF page count checked during build |

## Run the project

From the project root in PowerShell:

```powershell
.\.venv\Scripts\python -m streamlit run app.py
```

Choose the version and Gemini API in the sidebar, enter your key, load available models and select a compatible model. Offline demo makes no LLM requests and uses the validated Python engine in both versions. Changing the selected version/mode or pressing Restart resets the game.

## Reproduce the submission

```powershell
.\.venv\Scripts\python -m pip install -r requirements-dev.txt
.\.venv\Scripts\python scripts/build_submission.py
```

The builder runs the tests, executes seven offline comparisons, generates SVG and JPG diagrams and a three-page report, and creates `AI-Escape-Room-submission.zip`. `submission-manifest.json` records test counts and SHA-256 hashes of packaged files. The ZIP excludes the virtual environment, caches, actual secret files and empty IDE scratch file. Runtime requirements remain separate from optional report-building dependencies.

## Evidence and limits

The comparison results explicitly use simulated model errors to demonstrate why Version 1's architecture can accept a false result and Version 2's validators stop it. They do not claim that Gemini produced those injected responses. Real-provider adversarial results can be captured with the documented `--live` command. Provider access, quota and availability cannot be guaranteed by local code. The PDF report includes the provider failures observed in user-shared transcripts and the fixes implemented.
