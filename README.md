# Relay — Operations with accountability

Relay is a human-centered operations work queue built for the Newtonite Software Engineering Challenge. It focuses on the moments where ordinary task CRUD becomes unsafe: competing ownership claims, stale edits, approval boundaries, duplicate retries, and the need to explain past decisions.

## Project documentation

- [Architecture](ARCHITECTURE.md)
- [Engineering decisions and trade-offs](ENGINEERING_DECISIONS.md)
- [Known limitations](KNOWN_LIMITATIONS.md)
- [GitHub publishing checklist](GITHUB_PUBLISHING.md)

## Core design ideas

- Reject stale writes instead of silently overwriting another person's work.
- Claim ownership using a conditional update and support safe retries.
- Enforce roles and team/resource access on the server, not only in the UI.
- Treat approval as a workflow rule rather than a visual label.
- Keep a history of key operational decisions.

## Important status

This repository currently contains the project documentation and setup notes. The application source and automated tests still need to be added before this repository is a complete runnable submission. The demo design uses FastAPI, SQLite for local evaluation, a static HTML/CSS/JavaScript interface, and pytest.

## Intended local workflow

Once the application source is present, the expected setup is:

```bash
python -m venv .venv
# macOS/Linux
source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Then open <http://127.0.0.1:8000>. Tests are intended to run with `pytest -q`.

## Security note

The planned demo identity scheme uses fixed example tokens and is not production authentication. Do not deploy with real customer, payment, employee, or credential data. Review the implementation, run the tests, and make sure you can explain the design decisions before submitting.
