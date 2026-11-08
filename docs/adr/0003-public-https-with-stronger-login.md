# ADR-0003: Public HTTPS with a stronger login

- Status: Accepted
- Date: 2026-11-08
- Requirements: R-01, R-03, R-04, R-05, R-06, N-01

## Context

The owner wants access from any device, including ones that cannot have extra
software installed. The current protection is a single PIN with a global, in-memory
lockout. That was designed for a local-only app. On the public internet, automated
guessing starts within minutes of a server appearing, and a global lockout would let
a stranger keep the owner locked out.

## Decision

Expose the app publicly over HTTPS and replace the PIN with a proper login:
username and password stored with a modern slow hash, per-client and per-account rate
limiting that survives restarts, secure session cookies, and optionally TOTP
two-factor authentication. Real financial data is loaded only after this is in place.
Until then the server runs with demo data.

## Alternatives considered

- **Private access only (VPN such as Tailscale).** Smallest attack surface and least
  work, but requires the client software on every device and does not work from an
  arbitrary computer. It remains the fallback if the public approach proves too risky
  or burdensome.
- **Keep the PIN and add an authenticating proxy in front.** Cheaper, but leaves the
  app's own weaknesses in place and teaches less.
- **Third-party identity provider (OIDC).** Robust, but heavy for a single user and
  adds an external dependency.

## Consequences

- Authentication code is rewritten and must be well tested (R-03 to R-05). It is
  built on the multi-user model in ADR-0006: several accounts, created by an
  administrator, with limits that apply per account and per client.
- Any weakness here is exposed to the internet, so this phase precedes loading real
  data, and review of it is mandatory.
- The README's security section and offline claims must be updated.
- The decision is reversible: closing the public port and switching to VPN-only
  access needs only proxy and firewall changes.
