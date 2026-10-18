# Known limitations

1. **Demo identity only.** Fixed bearer tokens are public by design for local assessment. Anyone with access to the code can use them. Do not deploy with real data; replace with SSO/OIDC and secure session/token handling.
2. **SQLite concurrency and scale.** The assignment describes thousands of simultaneous users and a large activity history. This prototype does not claim to satisfy that production scale. Use PostgreSQL, migrations, pooling, load tests, and production observability.
3. **No real-time push.** Users refresh or reload to see another user's changes. WebSockets/SSE are intentionally not implemented.
4. **Limited collaboration.** No comments, mentions, file attachments, notifications, or background processing.
5. **Simple membership model.** Each demo user has one team; real multi-team membership and fine-grained resource permissions need a normalized membership model.
6. **Audit is useful, not tamper-proof.** Key actions are logged transactionally, but administrators with database access can modify SQLite data. Production audit needs restricted write access, retention rules, and potentially external immutable storage.
7. **Basic UI reconciliation.** Stale mutations are rejected and the detail panel reloads on a conflict, but there is no field-by-field merge interface.
8. **Date/time handling.** Due dates are simple ISO calendar dates; there is no timezone-aware scheduling or business-hours calendar.
9. **No production operations.** No deployment pipeline, backup/restore procedure, metrics exporter, alerting, or secret management is included.
10. **Test scope.** Tests focus on high-risk API behaviour. A production release would add browser-level tests, concurrent multi-process tests against PostgreSQL, schema migration tests, and broader authorization matrices.