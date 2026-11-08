# ADR-0007: Requirements are verified by tests and evidence, enforced in CI

- Status: Accepted
- Date: 2026-11-08
- Requirements: R-22, N-07, N-09

## Context

Traceability should not stop at "this change implements that requirement." A
requirement is only trustworthy if something shows it holds. Some requirements can be
checked by code (login limits, data isolation), some only against the running system
(HTTPS, open ports), and some only by a person doing a drill (restoring a backup,
hardening the server).

## Decision

Every requirement carries one or more verification methods:

- **T**: an automated test, run in CI on every change.
- **S**: a smoke test run against the deployed system after each deploy.
- **E**: a manual check or drill recorded in `docs/verification/`.

Mechanism:

- Tests cite requirements with a pytest marker, for example
  `@pytest.mark.requirement("R-04")`. A test may cite several.
- A script, `scripts/check_traceability.py`, reads the requirement IDs from
  `docs/requirements.md`, the markers from `tests/`, and the records from
  `docs/verification/`. It fails the build if a Must or Should requirement has no
  test or evidence, or if a marker cites an unknown ID. It regenerates
  `docs/traceability.md`.
- A requirement counts as *verified* only when its tagged tests pass or its evidence
  record is current. The definition of done for an issue includes this.
- Security requirements are verified with negative tests: the unauthorized action is
  shown to be refused.

## Alternatives considered

- **A test-management tool (TestRail, Xray).** Capable, but separate from the code
  and not free for private use.
- **Behaviour-driven tests (Gherkin with pytest-bdd).** Clearer to non-programmers,
  but more ceremony than a one-person project warrants.
- **Matching by test name or a hand-kept spreadsheet.** Silently goes out of date.

## Consequences

- The format of the requirement tables is now an interface: the script parses the ID
  column, so IDs must stay stable and in the first column.
- The script is code to maintain and test (R-22 covers it).
- Manual evidence depends on discipline. The matrix shows it as *stale* when it is old,
  but a person still has to redo it.
- Existing tests need tagging, and gaps in B-02 and B-04 need new tests first.
- Writing the tests and evidence is part of each phase's work, not a later phase.
