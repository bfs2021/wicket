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
- **Two ports, one per actor:** `Backlog` (submit, withdraw) for producers and `Ledger` (view, grant,
  renew, release) for pools, each with its own adapter class.
- **The store's obligations** are the contract every pair of adapters keeps, checked by
  `StoreContract`: one grant at a time; one clock, the store's (`clock_timestamp()` in PostgreSQL);
  expiry computed on read, never written; a consistent snapshot (one `REPEATABLE READ` transaction in
  PostgreSQL); leases matched on `(pool, id, token)`; grant history complete for a retention the view
  reports; pools that appear on first use; and a durable backlog that can join the caller's
  transaction.
- **Polling, not signals.** With nothing to grant the pool sleeps `poll` with jitter of up to half.

## Alternatives

- **The decision in the store.** Every factor would be rewritten in every adapter, and a caller's
  factor could not be expressed in SQL.
- **A leader process.** Elections and failover for a decision that a version check makes safe.
- **A bounded number of grant retries.** In simulation it made a burst of grants 20 times slower;
  every round already grants at least one ticket.

## Consequences

- A decision is O(waiting tickets): about 1.4 ms for 1k and 15 ms for 10k in simulation. Beyond that,
  shard pools.
- Concurrent workers of one pool conflict: a burst to 64 awake workers took about 10 views per grant,
  with no livelock and no starved worker.
- An idle pool reads its snapshot every `poll` per worker. A store-side wake-up can come later behind
  the same `permit()`.
