# Project documentation

This folder is the single source of truth for *why* and *how* the project is built.
Code says what the system does; these documents say what it should do, why it is
shaped this way, and how to operate it.

| Document | Purpose | Status |
|---|---|---|
| [vision.md](vision.md) | Problem, goals, scope, success criteria | Draft |
| [requirements.md](requirements.md) | Numbered requirements with acceptance criteria | Draft |
| [architecture.md](architecture.md) | Current and target architecture | Draft |
| [adr/](adr/README.md) | Architecture decision records (one file per decision) | Draft |
| [traceability.md](traceability.md) | Requirement-to-test/evidence matrix (generated once R-22 lands) | Draft |
| [verification/](verification/README.md) | Recorded evidence for manually verified requirements | Living |
| [learning-log.md](learning-log.md) | Personal journal: what was done, what was learned | Living |
| `runbooks/` | Step-by-step operating procedures (created in later phases) | Planned |

## Rules

- **Public repository.** Never put secrets, server IP addresses, SSH details,
  exact firewall rules, or real financial data in any file or issue. Server-specific
  values live in a password manager and in untracked files on the server.
- **Traceability.** Every requirement has an ID (`R-nn`). Every issue references the
  requirement it serves, and every pull request says `Closes #<issue>`.
- **Verification.** Every requirement is verified by an automated test, a smoke test,
  or a recorded manual check, and tests cite the requirement they prove. A
  requirement is not done until it is verified.
- **Decisions are append-only.** An ADR is never deleted. If a decision changes,
  write a new ADR that supersedes the old one.
- **Docs change with code.** A pull request that changes behaviour updates the
  affected document in the same pull request.
