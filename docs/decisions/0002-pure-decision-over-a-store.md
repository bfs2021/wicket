# 2. A pure decision over a store's snapshot, granted by version

**Status:** Accepted

## Context

The decision must hold its limits with any number of worker processes, and a caller must be able to
write a factor of its own. Three places for it were considered: a pure core over a snapshot, the
store (one SQL query), and a leader process.

## Decision

- **The decision is pure.** A `Pool` reads a `PoolView` from its `Ledger`, asks each `Limit`, lets its
  `Priority` choose, and calls `grant` with the view's `version` and the new `Fairness`.
- **A grant is a compare-and-swap on the pool's version.** It succeeds only if the version is
  unchanged and the ticket still waiting; it writes the permit, the grant's time and the `Fairness`
  together. Only a grant changes the version, and a `Limit` reads only what a grant changes, so no
  limit is exceeded and `Fairness` never forks. On `Conflict` the pool reads again at once.
- **One waiting call at a time per `Pool`.** The `permit()` calls of one `Pool` wait for a grant
  behind its lock, held while reading, granting and sleeping, so the workers of one process never
  conflict with each other and a process reads once per `poll`; only processes conflict.
- **Two ports, one per actor:** `Backlog` (submit, withdraw) for producers and `Ledger` (view, grant,
  renew, release) for pools, each with its own adapter class.
- **The store's obligations** are the contract every pair of adapters keeps, checked by
  `StoreContract`: one grant at a time; one clock, the store's (`clock_timestamp()` in PostgreSQL);
  expiry computed on read, never written; a consistent snapshot (in PostgreSQL one statement or one
  read-only `REPEATABLE READ` transaction; a grant in `READ COMMITTED` starts with the version's
  `UPDATE … WHERE version = :v`, which updates nothing under a concurrent grant); leases matched on
  `(pool, id, token)`; grant history complete for a retention the view reports; pools that appear
  on first use; a durable backlog that can join the caller's transaction; and a cancelled call that
  leaves the store usable.
- **Polling, not signals.** With nothing to grant the pool sleeps a random time between `poll / 2`
  and `poll`.

## Alternatives

- **The decision in the store.** Every factor would be rewritten in every adapter, and a caller's
  factor could not be expressed in SQL.
- **A leader process.** Elections and failover for a decision that a version check makes safe.
- **A bounded number of grant retries.** In simulation it made a burst of grants 20 times slower;
  every round already grants at least one ticket.

## Consequences

- A decision is O(waiting tickets): about 1.4 ms for 1k and 15 ms for 10k in simulation. Beyond that,
  shard pools.
- The processes of one pool conflict. On a PostgreSQL prototype 64 workers bursting took 31 views per
  grant without the lock and 3.9 with it, in 4 processes of 16; there is no livelock and no starved
  worker.
- An idle pool reads its snapshot every `poll` per process. A store-side wake-up can come later behind
  the same `permit()`.
