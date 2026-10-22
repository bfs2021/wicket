# Changelog

Notable changes to this project. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow
[semantic versioning](https://semver.org/spec/v2.0.0.html). While the version is `0.x` the public API
may change in a minor release.

This file is built from fragments in `changelog.d/` when a release is made; see
[CONTRIBUTING.md](CONTRIBUTING.md#changelog). Do not edit it by hand.

<!-- towncrier release notes start -->

## [0.1.0] - 2026-10-22

### Added

- The core: tickets with traits, fairness between tenants by Start-time Fair Queuing, priority from weighted factors (`FairShare`, `Age`, `Trait`), the `Concurrency` and `Rate` limits, the `Backlog` and `Ledger` ports with an in-memory store, and `Pool`, whose `permit()` leases a ticket to an `async with` block and releases it only when the block ends normally. ([#1](https://github.com/deyna256/wicket/issues/1))
- A PostgreSQL store in the extra `wicket[postgres]`: `PostgresBacklog` writes tickets in your SQLAlchemy session, in the same transaction as your own rows, and `PostgresLedger` keeps one queue, its limits and its fairness for every process; add `wicket.postgres.metadata` to your migrations. ([#3](https://github.com/deyna256/wicket/issues/3))
