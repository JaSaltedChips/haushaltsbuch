# ADR-0005: GitHub for project management and documentation

- Status: Accepted
- Date: 2026-11-08
- Requirements: R-09, N-07

## Context

The work should follow a real product process with every step traceable, using free
tools, for a one-person project whose code is already on GitHub.

## Decision

Use GitHub for all of it: Issues for work items, Milestones for phases, Projects for
the board, pull requests for review and history, Actions for CI/CD, Releases and tags
for versions, and a `docs/` folder in the repository for documentation and ADRs
("docs as code"). Commit messages keep the conventional prefix style and reference an
issue number. Pull requests close their issue.

## Alternatives considered

- **Jira + Confluence.** Capable, but a second system to keep in sync and more than a
  single person needs.
- **GitLab.** Similar all-in-one scope, but the code and CI are already on GitHub.
- **Notion, Trello, Linear.** Convenient, but separate from the code, so links
  between decisions, issues, and commits are weaker.

## Consequences

- Traceability is a chain of links inside one system:
  requirement → issue → branch → commits → pull request → release, with tests and
  evidence attached to the requirement (ADR-0007).
- The repository is public, so issues, documents, and pull requests must contain no
  secrets, addresses, or sensitive operational detail.
- Documentation is versioned with the code and reviewed in the same pull requests.
