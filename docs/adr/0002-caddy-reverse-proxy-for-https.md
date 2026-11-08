# ADR-0002: Caddy reverse proxy for HTTPS

- Status: Accepted
- Date: 2026-11-08
- Requirements: R-01, N-01, N-02

## Context

The application speaks plain HTTP and should not handle certificates itself. On the
public internet, all traffic must be encrypted, certificates must renew without
manual work, and the application port must not be exposed directly.

## Decision

Place Caddy in front of the application as a reverse proxy in the same Docker Compose
project. Caddy terminates TLS using automatically issued and renewed certificates,
redirects HTTP to HTTPS, sets security headers, and forwards requests to the
application over the private Docker network. Only Caddy publishes ports.

## Alternatives considered

- **nginx + certbot.** Widely used, but certificate issuance and renewal are separate
  moving parts to configure and monitor.
- **Traefik.** Strong with many dynamic services; unnecessary for one service.
- **Terminating TLS in the application (uvicorn).** Mixes concerns and lacks
  automatic renewal.
- **Provider or CDN-managed TLS (for example a proxying DNS service).** Convenient,
  but adds a third party that sees all plaintext traffic and hides the mechanism the
  project aims to learn.

## Consequences

- Certificates are automatic, which removes a common cause of outages.
- The Compose file changes: the application stops publishing a host port; the proxy
  publishes ports 80 and 443.
- A DNS record pointing at the server is required before certificates can be issued.
- Caddy's configuration and data volume (certificates) must be backed up or be
  reproducible.
