# Verification evidence

Requirements verified by method **E** (manual check or drill) are evidenced by one
record per check in this folder. Automated tests (**T**) and smoke tests (**S**) do
not need a record here: their evidence is the CI run.

## File name

`R-nn-YYYY-MM-DD.md` (or `N-nn-...`), for example `R-08-2026-12-01.md`.

## Template

```markdown
# R-nn: <requirement title>

- Date: YYYY-MM-DD
- Verified by: <name or handle>
- Version / commit under test: <tag or short hash>
- Result: Pass | Fail

## Procedure
The steps actually performed, specific enough that someone else could repeat them.

## Observations
What was seen, measured, or timed (for example: restore took 22 minutes).

## Evidence
Link to command output, logs, or a screenshot. Redact anything sensitive.

## Follow-ups
Issues opened for anything that failed or was surprising.
```

## Rules

- This repository is public. Evidence must not contain secrets, IP addresses, SSH
  details, hostnames beyond the public domain, or real financial data. Redact first.
- A failed check is recorded, not deleted. Open an issue and re-verify after the fix.
- Re-verify when the checked thing changes materially, and at least yearly for
  recovery and hardening items.
