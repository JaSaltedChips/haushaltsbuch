# Vision

Status: Draft · Last updated: 2026-11-08

## Problem

Expense Monitor is a personal household-finance tracker (Python, FastAPI, SQLite).
It currently runs on one laptop, bound to the local network interface. That causes
two problems:

1. **Availability.** When the laptop is off or asleep, the app is unreachable. Entries
   cannot be made on the go.
2. **Access.** It can only be reached from the home network (or, unencrypted, from a
   phone on the same Wi-Fi).

## Goal

Run Expense Monitor on an always-on cloud server so its users (at least two) can use
it securely from any device, anywhere, at any time, each with private data that is
protected and recoverable.

## Secondary goal: learning

The project is also a deliberate, hands-on way to learn backend and cloud
engineering by building and operating a real service. The process (requirements,
design records, issues, pull requests, CI/CD, runbooks) is part of the goal, not
overhead. Decisions favour *understanding the mechanism* over the shortest path
(for example: a plain Linux server rather than a managed platform that hides it).

## Users

At least two people, one of whom is the administrator (the owner). Accounts are
created by the administrator; there is no public sign-up. Each user's financial data
is private to them (see [ADR-0006](adr/0006-multi-user-with-isolated-data.md)).

## Scope

In scope:

- Hosting on a rented Linux server (VPS) in the EU
- Domain name and HTTPS
- Multiple user accounts with strict data isolation, plus basic user administration
- Stronger authentication suitable for the public internet
- Automated, encrypted, off-site backups with a tested restore
- Automated testing and deployment (CI/CD)
- Requirement-level verification: every requirement is tied to a test or recorded
  evidence, enforced in CI
- Basic monitoring and operating runbooks

Out of scope (for now):

- Sharing data between users (shared household ledgers) and roles beyond
  administrator and user
- Self-service sign-up
- Bank API integration or automatic import
- Native mobile apps
- High availability, clustering, Kubernetes
- Replacing SQLite (see ADR-0004)

## Success criteria

The project is successful when all of these hold:

1. Two users open `https://<own domain>` on a phone and a laptop and use the app
   normally while the laptop at home is switched off.
2. Neither user can see or change the other's data, shown by automated tests.
3. A restore of the latest backup onto a fresh server has been performed and verified.
4. A `git push` that passes the tests deploys without manual server work.
5. Repeated wrong logins from the internet do not succeed and do not lock real users
   out.
6. Every requirement is verified by an automated test or a recorded check, and CI
   fails if one is not. Every change is traceable from requirement to issue to pull
   request to test to release.

## Constraints

- Budget: at most about €10 per month all-in (server, domain, backup storage).
- Data location: financial data stays in the EU.
- Time: part-time, done in small increments (one phase at a time).
- The repository is public, so all documentation and issues must be safe to publish.
