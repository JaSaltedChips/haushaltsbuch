# ADR-0004: Keep SQLite as the database

- Status: Accepted
- Date: 2026-11-08
- Requirements: R-07, R-08, N-03, N-06

## Context

Moving to a server raises the question of whether to switch to a client/server
database such as PostgreSQL. The app has exactly one user, low write volume, and a
small dataset.

## Decision

Keep SQLite, stored in a Docker volume, with one application process.

## Alternatives considered

- **PostgreSQL.** The usual choice for multi-user services and a good thing to learn,
  but it adds a second service to run, secure, upgrade, and back up, with no benefit
  at this scale.
- **Managed database from the provider.** Extra cost and a dependency without a
  matching need.

## Consequences

- Backups are simple: use SQLite's online backup mechanism to get a consistent copy
  while the app runs.
- One application process only. Today sessions and login limits are held in memory,
  which also requires a single worker. R-04 and R-05 move limits and sessions into
  storage that survives restarts.
- Two users (ADR-0006) are well within what SQLite handles. Enable write-ahead
  logging, keep one application process, and test concurrent use (N-10).
- If the project grows to many users or needs several processes, this decision
  should be revisited by a new ADR that supersedes this one.
