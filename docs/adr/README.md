# Architecture decision records (ADRs)

An ADR captures one significant decision: the context, what was chosen, what was
rejected, and the consequences. They are short, numbered, and never deleted.

## Index

| ADR | Title | Status |
|---|---|---|
| [0001](0001-host-on-a-vps.md) | Host on a rented Linux VPS | Accepted |
| [0002](0002-caddy-reverse-proxy-for-https.md) | Caddy reverse proxy for HTTPS | Accepted |
| [0003](0003-public-https-with-stronger-login.md) | Public HTTPS with a stronger login | Accepted |
| [0004](0004-keep-sqlite.md) | Keep SQLite as the database | Accepted |
| [0005](0005-github-for-project-management.md) | GitHub for project management and docs | Accepted |
| [0006](0006-multi-user-with-isolated-data.md) | Multiple users with isolated data in one database | Accepted |
| [0007](0007-requirements-verified-by-tests-and-evidence.md) | Requirements are verified by tests and evidence, enforced in CI | Accepted |

## Statuses

`Proposed` → `Accepted` → (`Deprecated` or `Superseded by ADR-NNNN`)

## Writing a new one

Copy this template to `NNNN-short-title.md` using the next number:

```markdown
# ADR-NNNN: Title

- Status: Proposed
- Date: YYYY-MM-DD
- Requirements: R-nn, N-nn

## Context
What problem or force makes a decision necessary?

## Decision
What we will do, in one or two sentences.

## Alternatives considered
Each with the main reason it was not chosen.

## Consequences
What becomes easier, what becomes harder, what we must now do or watch.
```
