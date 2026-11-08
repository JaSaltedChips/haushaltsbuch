# ADR-0006: Multiple users with isolated data in one database

- Status: Accepted (private ledgers and administrator-as-normal-user confirmed by the owner, 2026-11-09)
- Date: 2026-11-08
- Requirements: R-17, R-18, R-19, R-20, R-21, N-09, N-10

## Context

The app must support at least two users from the start. Today it has no concept of a
user: the `accounts`, `categories`, `transactions`, and `settings` tables have no
owner, and the PIN hash is a global setting. The app is named for a *household*
ledger, so it is not obvious whether two users should share data or each keep their
own. The safe and simplest reading is that each user keeps a private ledger; sharing
can be added later deliberately.

## Decision

- Each user has a private ledger. No data is shared between users.
- Users are created by an administrator. There is no public sign-up. The first
  account created on first run is the administrator.
- The administrator is also a normal user with their own private ledger. The
  administrator role adds user management and the whole-database download; it does
  not add access to other users' ledgers through the web interface.
- All data tables get a `user_id` column. Every data-access function takes the
  current user's ID as a required parameter and filters on it. There is no function
  that reads or writes user data without one.
- The application layer derives the user from the authenticated session, never from
  a request parameter.
- Cross-user access is refused as "not found", so responses do not reveal which IDs
  exist.
- Existing data is migrated to the first (administrator) user.
- The whole-database download is limited to the administrator (R-21).

## Alternatives considered

- **One SQLite database file per user.** Isolation by construction and per-user
  backups, but a shared users database is still needed, migrations must run against
  every file, and administrator tasks and reporting across files get awkward. A
  reasonable choice that remains open if the `user_id` approach proves error-prone.
- **Shared household ledger (all users see the same data).** Simpler, but it is a
  different product decision, and it would be hard to unwind into private ledgers
  later. Left out of scope; it can be added as an explicit sharing feature.
- **Separate deployments per user.** Strongest separation, but doubles the operating
  work for no benefit at this scale.

## Consequences

- The most likely class of bug is a missing user filter on one query (an "insecure
  direct object reference"). It is mitigated by the required-parameter design and,
  above all, by tests: every route that handles user data gets an authorization test
  using two users (N-09, R-18).
- The schema changes in every table and a migration is needed (R-19). It is tested
  on a fixture and rehearsed on a copy of the real database, with a backup taken
  first.
- Uniqueness rules (for example account and category names) become per-user.
- Rate limiting and lockouts become per account and per client (R-04), so one user
  cannot lock out the other.
- With two users, concurrent writes are possible but rare. SQLite handles this with
  write-ahead logging and a single application process (see ADR-0004, N-10).
- Documentation, README, and the PIN-related screens change accordingly.
