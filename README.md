# Relay — Operations with accountability

Relay is a human-centered operations work queue built for the Newtonite Software Engineering Challenge. It focuses on the moments where ordinary task CRUD becomes unsafe: competing ownership claims, stale edits, approval boundaries, duplicate retries, and the need to explain past decisions.

## Features

- Team-scoped queue with search, state filters, priority ordering, and bounded pagination.
- Server-side role and resource checks.
- Version-based stale-write rejection.
- Conditional ownership claims and idempotency keys for retry safety.
- Explicit workflow transitions and independent approval before resolving flagged work.
- Activity history for key decisions.
- Responsive browser UI and demo role switcher.

## Run locally

Requires Python 3.10+.

```bash
python -m venv .venv
# macOS/Linux
source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open <http://127.0.0.1:8000>. API docs are at <http://127.0.0.1:8000/docs>. The app seeds fictional example requests on first run. Set `RELAY_DB_PATH` to choose another database file.

## Run tests

```bash
pytest -q
```

The tests cover stale edits, viewer restrictions, and approval gates.

## Demo identities

Select a profile in the top-right menu. For direct API calls, use `Authorization: Bearer tok-manager` or another token below.

| Token | Role | Team |
|---|---|---|
| `tok-analyst` | Analyst | Payments |
| `tok-operator` | Operator | Operations |
| `tok-manager` | Manager | Management |
| `tok-viewer` | Viewer | Operations |

These fixed tokens are for local demonstration only, not production authentication.

## Documentation

- [Architecture](ARCHITECTURE.md)
- [Engineering decisions and trade-offs](ENGINEERING_DECISIONS.md)
- [Known limitations](KNOWN_LIMITATIONS.md)
- [Publishing checklist](GITHUB_PUBLISHING.md)



Before submitting, run the app and tests yourself, review the authorization and concurrency behaviour, and make sure you can explain the design choices. Do not enter real customer, payment, employee, or credential data.
