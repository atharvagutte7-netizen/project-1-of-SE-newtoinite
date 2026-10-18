# Architecture

```text
Browser (HTML/CSS/JavaScript)
  |  bearer demo token + JSON
  v
FastAPI routes
  |-- identity and role checks
  |-- resource/team scope checks
  |-- workflow validation
  |-- version / idempotency checks
  v
SQLite (local evaluation)
  |-- work_items: current state + version
  |-- activity: decision history
  |-- idempotency: safe retry response
```

## Mutation sequence

1. Authenticate the demo identity.
2. Check the role and the user's access to the item/team.
3. Read the current record and compare the caller's version where applicable.
4. Validate the requested state transition or approval rule.
5. Apply a conditional write and append the activity record in the same transaction.
6. Return the authoritative server representation. A conflict returns HTTP 409 and the client refreshes rather than pretending its optimistic change succeeded.

## Concurrency notes

- Stale edits use a version predicate in the update statement.
- Claims use a single conditional update checking the observed version and unassigned/current-owner condition.
- Idempotency keys make repeat claim requests return the original successful response.
- SQLite's locking behaviour is adequate for a small local demo, not evidence of production-scale concurrency. PostgreSQL transactions and row-level locking/conditional updates should be load-tested for the production target.

## Data model

- `work_items`: title, context, team, category, priority, state, owner, due date, approval requirement, version, and timestamps.
- `activity`: actor, action, explanation, and timestamp for key changes.
- `idempotency`: request key, actor, action, stored response, and timestamp.

The list endpoint filters and paginates in SQL, orders by priority and update time, and does not load all rows into the browser.