# 5. Work is leased, delivered at least once and fenced by a token

**Status:** Accepted

## Context

A worker can die, hang or lose the store while it holds work. The work must not be lost, and an old
worker that wakes up must not overwrite the result of the worker that took the ticket after it.

## Decision

- **A permit is a lease** that `pool.permit()` renews every `lease / 3` while the block runs. A
  renewal that fails on a connection error is retried every `lease / 30` until the lease would end,
  measured on the worker's monotonic clock.
- **A lost lease cancels the block** with `LeaseLostError` and **releases nothing**, so the ticket is
  delivered again. `LeaseLostError` means only that.
- **Expiry is the store's.** Once the store's clock passes the lease end the ticket is waiting again,
  with its `submitted_at` and grant count kept.
- **A late release succeeds** while no one has leased the ticket again; it only lowers the leased
  count, so it cannot break a limit. After a re-grant or a withdrawal it answers `LeaseLost` and
  nothing is raised.
- **The token is the pool's version after the grant,** increasing within the pool. The caller stores
  it with its row and rejects a write that carries an older one.
- **When to give up is the caller's,** from `permit.attempt`.

## Alternatives

- **Release on a lost lease.** In simulation it dropped work that was never finished.
- **Exactly once.** It needs the store and the work in one transaction, which wicket does not own.

## Consequences

- The caller's work must be idempotent.
- A hung worker whose lease expired may still run, so real concurrency can exceed `Concurrency(n)`
  until it stops. A body that blocks the event loop cannot be cancelled and stops its own renewals.
