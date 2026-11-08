# Requirements

Status: Draft · Last updated: 2026-11-08

Priorities use MoSCoW: **M**ust, **S**hould, **C**ould. "Phase" refers to the
delivery phases in the project plan (GitHub milestones). Phase 4 is split: **4a**
is the multi-user data model, **4b** is authentication hardening.

## How to read this

- Each requirement has a stable ID. IDs are never reused.
- Each has acceptance criteria: observable checks that decide whether it is done.
- Each has a **verification method** (below). A requirement is only *done* when it is
  *verified*.
- Issues cite requirement IDs, pull requests close issues, and tests cite requirement
  IDs. That is the trace. See [ADR-0007](adr/0007-requirements-verified-by-tests-and-evidence.md)
  and the generated matrix in [traceability.md](traceability.md).

## Verification

| Code | Method | Where the evidence lives |
|---|---|---|
| **T** | Automated test run in CI on every change | Tests marked `@pytest.mark.requirement("R-nn")` |
| **S** | Smoke test run against the deployed system after each deploy | `tests/smoke/`, tagged the same way |
| **E** | Manual check or drill, with recorded evidence | `docs/verification/R-nn-YYYY-MM-DD.md` |

Rules:

1. Every requirement (baseline, functional, non-functional) has at least one method.
2. Every Must and Should requirement has at least one test or evidence record before
   its issue can close. Could requirements may be verified later.
3. CI fails if a requirement has no verification, or a test cites an ID that does not
   exist (see R-22).
4. Evidence (**E**) goes stale: it must be redone when the thing it checks changes
   materially, and at least yearly for recovery and hardening items.
5. Negative cases count. Requirements about security are verified by showing the bad
   thing is *refused*, not only that the good thing works.

## Baseline (already implemented)

These exist today and must keep working. Their tests exist in part and still have to
be tagged and completed.

| ID | Requirement | Verif. | Current test coverage |
|---|---|---|---|
| B-01 | Record transactions singly or in batch from a text note | T | Parser and accounting tests exist; HTTP-level tests are missing |
| B-02 | Manage accounts and categories | T | **No dedicated tests** |
| B-03 | Monthly report with charts, totals, and print/PDF output | T, E | Report and chart tests exist; print/PDF is manual |
| B-04 | CSV export and database backup download | T | **No dedicated tests** |
| B-05 | Mobile-friendly layout with hamburger menu | E | Manual check on a phone and a narrow window |
| B-06 | Automated test suite, run in CI | T | Workflow exists |

## Functional requirements (new)

| ID | Pri | Phase | Requirement | Acceptance criteria | Verif. |
|---|---|---|---|---|---|
| R-01 | M | 3 | Reach the app from anywhere over HTTPS using a domain name | App loads at the domain from a phone on mobile data and from a laptop on another network; certificate is valid; plain HTTP redirects to HTTPS | S, E |
| R-02 | M | 2 | App runs on an always-on server, independent of the laptop | App responds after the laptop is powered off; container restarts automatically after a server reboot | S, E |
| R-03 | M | 4b | Log in with username and password, replacing the PIN | Password stored with a modern slow hash (Argon2id or equivalent); first run creates the initial administrator; no public sign-up route exists; the PIN login is removed | T |
| R-04 | M | 4b | Brute-force protection suited to the public internet | Failed attempts are rate-limited per client address and per account; one user's failures never lock out another user and a remote attacker cannot lock out a user from other addresses; limits survive an app restart | T |
| R-05 | M | 4b | Secure session handling | Cookies are `Secure`, `HttpOnly`, `SameSite`; sessions expire; logout invalidates the session server-side; a disabled user's sessions end | T |
| R-06 | S | 4b | Two-factor authentication (TOTP) | Login requires a time-based one-time code once enabled; recovery codes exist | T |
| R-07 | M | 5 | Automated daily backups, encrypted, stored off the server | A scheduled job produces a consistent SQLite backup, encrypts it, uploads it elsewhere, and reports failure; retention keeps at least 30 days | T (script), E |
| R-08 | M | 5 | A documented, tested restore procedure | A runbook exists; the restore has been performed onto a clean environment and the data was verified to match | E |
| R-09 | M | 6 | Tests gate every change | A pull request cannot be merged while tests fail | E |
| R-10 | S | 6 | Deploy automatically after a successful merge | A merge to the main branch updates the server without manual steps; a failed deploy leaves the previous version running | S, E |
| R-11 | S | 6 | Roll back to a previous release quickly | A runbook describes it; it has been exercised once | E |
| R-12 | S | 7 | Uptime monitoring with notification | An external check alerts the owner within 10 minutes of an outage | E |
| R-13 | S | 6 | Running version is identifiable | The deployed version (tag or commit) is visible to the administrator and matches a release | T, S |
| R-14 | M | 1 | Server access is hardened | Key-only SSH; no root login; firewall allows only required ports; automatic security updates enabled | E |
| R-15 | M | all | No secrets in the repository | A secret scan runs in CI and fails the build if a secret is committed | T |
| R-16 | C | 4b | Remove runtime dependence on third-party scripts | Charts load without fetching code from a public CDN (the Sankey diagram currently loads Plotly from one) | T |
| R-17 | M | 4a | Multiple user accounts, at least two | An administrator creates user accounts; at least two users can be active at the same time; there is no public sign-up; the administrator is also a normal user with their own private ledger | T |
| R-18 | M | 4a | Each user's data is private to them | Every account, category, transaction, setting, report, and export belongs to exactly one user. A user can never read or change another user's data through any page or API call, including by guessing identifiers; such attempts are refused without revealing that the record exists | T |
| R-19 | M | 4a | Existing data migrates to the first user without loss | A migration moves the current single-user database to the new model; row counts and balances match before and after; verified on a copy of the real database before production | T, E |
| R-20 | S | 4b | Administrator manages users | The administrator can disable a user and reset their password; a disabled user cannot log in and active sessions end; the last administrator cannot be removed | T |
| R-21 | M | 4a | Backup and export respect user boundaries | A user can export only their own data. The whole-database download is limited to the administrator (or removed from the web interface in favour of the server-side backup) | T |
| R-22 | M | 0 | Every requirement is verified, and CI proves it | A script maps requirements to tests and evidence; CI fails when a Must or Should requirement has neither, or when a test cites an unknown ID; the matrix in `docs/traceability.md` is generated from it | T |

## Non-functional requirements

| ID | Category | Requirement | Verif. |
|---|---|---|---|
| N-01 | Security | TLS 1.2 or newer; HSTS enabled; sensible security headers (including a Content-Security-Policy) | S |
| N-02 | Security | Only ports 80 and 443 (plus the hardened SSH port) are reachable from the internet; the application port is not | S, E |
| N-03 | Availability | Best effort for a personal service; target 99% monthly, no redundancy required | E |
| N-04 | Recovery | Recovery point objective 24 hours; recovery time objective 4 hours | E |
| N-05 | Privacy | Server, storage, and backups are located in the EU | E |
| N-06 | Cost | At most about €10 per month all-in | E |
| N-07 | Maintainability | New behaviour ships with automated tests; documentation is updated in the same pull request | T (via R-22), E |
| N-08 | Observability | Application and proxy logs are retrievable for at least 14 days | E |
| N-09 | Security | Every route is covered by an authentication test (anonymous access refused) and every route that handles user data by an authorization test (another user's data refused). A test enumerates all routes and fails if one is not covered | T |
| N-10 | Integrity | Concurrent use by two users does not corrupt or lose data | T |

## Known gaps in the current implementation

Recorded here so they are fixed deliberately rather than discovered later. All of
this is visible in the public source.

- Authentication is a single PIN. The README documents this as acceptable only for
  local use.
- There is no concept of a user. The `accounts`, `categories`, `transactions`, and
  `settings` tables have no owner, and the PIN hash is a global setting (see R-17,
  R-18, R-19).
- The backup endpoint returns the whole database file. With several users that would
  hand one user every other user's data (see R-21).
- Failed-login lockout is global, not per client, and held in memory. On the public
  internet a stranger could keep users locked out; the counter also resets on restart
  (see R-04).
- Sessions are held in memory and lost on restart, which also forces a single worker
  process (see R-05 and ADR-0004).
- The database file is not encrypted at rest; protection relies on the server's
  access controls and on encrypted backups (see R-07).
- Test coverage is uneven: accounting, parsing, and reports are well covered, while
  account/category management, export, backup, and the HTTP layer are barely tested
  (see B-01, B-02, B-04, N-09).
- The README states that data stays on the PC and the app is offline. That will no
  longer be true and must be updated when the cloud deployment lands.

## Out of scope

Shared household ledgers (users seeing each other's data), fine-grained roles beyond
administrator and user, self-service sign-up, bank integrations, native apps, high
availability, and replacing SQLite. See [vision.md](vision.md).
