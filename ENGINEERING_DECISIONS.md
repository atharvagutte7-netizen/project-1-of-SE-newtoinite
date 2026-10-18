# Engineering decisions

This document explains the important trade-offs in Relay rather than claiming that the choices are universally correct.

## 1. A work item is a durable operational record, not a disposable task

**Decision:** Keep the current state in `work_items` and append meaningful changes to `activity` in the same database transaction.

**Why:** The team needs to understand who did what and why. A mutable row alone cannot explain a handoff or approval decision. The activity table provides a readable trail without requiring every list view to reconstruct the current state from events.

**Trade-off:** This is a practical hybrid, not a full event-sourced architecture. The activity log records key decisions, but it is not a complete replayable event stream. For production, audit immutability, retention, and transaction boundaries would need additional review.

## 2. Reject stale edits instead of silently picking a winner

**Decision:** Every work item has a monotonically increasing `version`. Mutations include the version they observed and update with `WHERE id = ? AND version = ?`.

**Why:** If two people edit the same item, the second writer must not unknowingly erase the first person's work. A `409 Conflict` gives the client a clear signal to reload and reconcile.

**Trade-off:** Users may need to retry a legitimate edit. This is preferable to silent data loss for operational work. A richer UI could offer a field-level merge experience later.

## 3. Claim ownership with a conditional write and make retries idempotent

**Decision:** Claiming is one conditional SQL update that checks both version and current owner. A client-supplied idempotency key stores the successful response for safe retries.

**Why:** A read-then-write sequence by itself has a race: two users can both read “unassigned.” The conditional write makes the database decide the winner. Idempotency protects against a repeated request after a timeout.

**Trade-off:** Idempotency records need a retention policy and careful scoping in production. This demo stores keys in SQLite and returns the saved response for a repeated key by the same actor.

## 4. Permissions live on the server and are checked at resource level

**Decision:** Demo roles are analyst, operator, manager, and viewer. Non-managers see and mutate only items in their team; only managers can make approval decisions. The UI also hides actions the user cannot take, but that is convenience, not security.

**Why:** A user can call an API without using the interface. Each endpoint must independently check identity, role, and team scope.

**Trade-off:** The team model is deliberately simple: one demo team per user. Real organizations need membership tables, explicit permissions, identity-provider integration, and possibly separation-of-duty policies per request type.

## 5. Approval is a workflow boundary, not a visual label

**Decision:** Items marked `approval_required` cannot transition to resolved until an independent manager approves them. The creator and current assignee cannot approve their own request. Rejection sends the item back to `in_progress` and records the reason.

**Why:** The brief includes payment investigations, compliance requests, and work requiring approval. A label that does not constrain server behaviour creates false confidence.

**Trade-off:** This is a small illustrative policy. Production approval may require configurable thresholds, multiple approvers, escalation, delegation, and separation of duties by risk class.

## 6. Keep the first deployment easy to run; state the scale boundary honestly

**Decision:** Use FastAPI, a small static frontend, and SQLite for local evaluation. Add indexes for common filtering paths and enforce bounded pagination on the API.

**Why:** A reviewer should be able to run and inspect the application in minutes. Pagination prevents the browser from loading the entire dataset.

**Trade-off:** SQLite is not the production choice for hundreds or thousands of concurrent users. A production deployment should move to PostgreSQL, use migrations, add connection pooling, observe query plans, and load-test realistic concurrent workloads. The assignment's expected scale is a design target, not a claim that this local prototype already meets it.

## Intentionally not built

- Real SSO, invitation flows, password reset, or account provisioning.
- External notifications or background workers.
- File attachments, comments, and rich-text collaboration.
- Configurable workflow designer or multi-step approval chains.
- Production deployment automation, monitoring, backups, or a formal data-retention policy.

These omissions keep the submission focused on correctness paths that can be demonstrated and tested in the assessment window.