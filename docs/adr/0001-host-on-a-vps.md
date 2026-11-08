# ADR-0001: Host on a rented Linux VPS

- Status: Accepted
- Date: 2026-11-08
- Requirements: R-01, R-02, N-05, N-06

## Context

The app must be reachable from anywhere and independent of the owner's laptop. It is
a small app for two or a few users, with one container and a small SQLite database. A second goal is to
learn backend and cloud operations hands-on.

## Decision

Run the existing Docker container on a small rented Linux virtual server (VPS) from
an EU provider. The first choice is Hetzner Cloud, in a German or Finnish location.

## Alternatives considered

- **Keep running on the laptop.** Fails the always-on requirement.
- **Raspberry Pi at home.** Always on and cheap, but needs a way through the home
  router (changing address, possible carrier-grade NAT), depends on home power and
  internet, and puts the home network at risk. Kept as an optional later exercise.
- **Platform-as-a-service (Fly.io, Render, Railway).** Fastest to start, but hides
  the server, networking, and TLS work that the learning goal is about, and ties the
  setup to one platform's tooling.
- **Large clouds (AWS, GCP, Azure).** Powerful but disproportionately complex and
  easy to misconfigure for one small app.

## Consequences

- The owner is responsible for the operating system, patching, firewall, backups,
  and monitoring. These become requirements (R-07, R-08, R-12, R-14).
- Cost is low and predictable (a few euros per month).
- Because the app is containerised, moving to another provider (or to a Raspberry
  Pi) later is a small change. Provider choice is therefore reversible.
