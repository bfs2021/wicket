# Security policy

## Supported versions

While the version is `0.x`, only the latest release receives security fixes.

## Reporting a vulnerability

Report it privately through
[GitHub's vulnerability reporting](https://github.com/deyna256/wicket/security/advisories/new),
not in a public issue. Include the affected version, what an attacker can do and the steps to reproduce it.
Keep real credentials, connection strings and ticket data out of the report.

## What wicket trusts

- **Factors and limits of the caller's are the caller's code.** wicket runs them in the worker's
  process, as it runs any other code of the caller. A ticket's traits are checked to be in `0..1`.
- **The store is trusted.** What a `Ledger` reports — waiting tickets, leases, the version, the time —
  decides every grant. Whoever can write to the store's tables can grant any ticket.
- **Tickets hold what the caller puts in them.** wicket stores a ticket's id, tenant and traits and
  never logs them.

Relevant areas include how the PostgreSQL store builds its queries and whether a stale permit can
still act after its lease was granted to another worker.
