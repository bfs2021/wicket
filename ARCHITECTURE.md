# Architecture

This document is for people who change wicket's code. It describes how the code is laid out and the
rules that hold everywhere in it. Why the main choices were made is in [docs/decisions](docs/decisions/).

**Nothing is built yet.** The code map below is the planned layout; the invariants already hold for
the first line of code.

## Bird's eye view

wicket decides which waiting ticket of a pool may start now. Producers submit tickets to a `Backlog`;
workers ask a `Pool` for a permit. To grant one, the pool reads a snapshot of itself from its
`Ledger`, asks its limits whether one more may start, lets its priority choose the ticket, and writes
the grant only if the snapshot's version is still current. The worker holds the permit as a lease
that the pool renews until the work is done.

```text
producer ──▶ Backlog.submit ──▶ store ◀── Ledger.view / grant / renew / release ◀── Pool.permit() ◀── worker
                                                       │
                                     PoolView ──▶ Limit.admits, Priority.first (Factor.scores), Fairness.after
```

The decision is a pure function of a `PoolView`; only the store does I/O.

## Code map

Planned; all code will be in `src/wicket/`.

| part | what is there |
|---|---|
| core | the values `Ticket`, `Waiting`, `Permit`, `PoolView`, `Version`, `Fairness` and the result values; the contracts `Factor`, `Limit`, `Backlog`, `Ledger`; `Priority`; `Pool` |
| factors and limits | `FairShare`, `Age`, `Fact`; `Concurrency`, `Rate` |
| in-memory store | `MemoryState`, and its two adapters `MemoryBacklog` and `MemoryLedger` |
| `StoreContract` | the test suite every pair of store adapters passes |
| `postgres` extra | `PostgresBacklog` on the caller's session and `PostgresLedger` on its own engine |

The public API will be `wicket.__all__`. Everything else may change without notice.

## Invariants

wicket follows the ideas of *Elegant Objects* by Yegor Bugayenko, in idiomatic Python. These rules hold
in all of `src/wicket/`.

1. **A class stands for a thing in the problem, not an action:** a ticket, a pool, a limit, a ledger.
   There are no `*Manager`, `*Scheduler` or `*Service` classes, no static methods and no module-level
   functions with logic.
2. **Objects do not change after construction.** Classes are `msgspec.Struct` with `frozen=True`. A
   constructor stores its arguments and may reject a value the object cannot represent (ValueError);
   it never does work. A new state is a new object: `Fairness.after` returns one.
3. **An interface (`typing.Protocol`) exists only where there are two implementations or more:**
   `Factor`, `Limit`, `Backlog` and `Ledger`.
4. **New behaviour is a wrapper, not a flag or a subclass.** Observation, for one, is the caller's
   wrapper around its `Backlog` and `Ledger`. Only exceptions inherit, from `Exception`.
5. **"No value" is an object, not `None`.** An outcome is a result value — `Conflict`, `LeaseLost`,
   `NoTicket` and the rest — that the caller matches on; `None` is not a result.
6. **The decision is pure.** `Limit.admits`, `Factor.scores`, `Priority.first` and `Fairness.after`
   read a `PoolView` and return a value: no I/O, no clock, no randomness. A `Limit` reads only what a
   grant changes — `leased`, `grants` and `now` — so the version check keeps every limit.
7. **One clock, the store's.** Every moment in a view comes from the store. The only other clock is the
   worker's monotonic clock, for when to renew its lease.
8. **Each port has its own adapter.** Producers and workers change for different reasons, so a store
   brings a `Backlog` class and a `Ledger` class that share only its data.
9. **The library does not print or log.** It returns values and raises errors; observing them is the
   caller's.
10. **Types are checked on data, never on behaviour.** `match` reads the closed unions of results;
    objects with behaviour are called through their interface.

**Where wicket departs from *Elegant Objects*:**

- **Data has public fields.** `Ticket`, `Waiting`, `Permit` and `PoolView` are immutable records with
  public fields; accessor methods would be noise in Python.
- **A permit is held with `async with`**, Python's usual "take, use, give back".
- **The in-memory store changes inside**, behind its lock; its state never leaves it except as views.

## Cross-cutting concerns

**Concurrency.** Every grant is a compare-and-swap on the pool's version; nothing else changes it, so
heartbeats and submissions never make grants conflict. The `permit()` calls of one `Pool` wait for
a grant one at a time behind its lock, so only processes conflict and a process reads once per
`poll`. On a conflict the pool reads again at once; with nothing to grant it sleeps a random time
between `poll / 2` and `poll`
([decision 2](docs/decisions/0002-pure-decision-over-a-store.md)).

**Failure.** Delivery is at least once. A lost lease cancels the worker's block with
`LeaseLostError` and releases nothing, so the ticket is delivered again; the permit's token lets the
caller reject the old worker's late write ([decision 5](docs/decisions/0005-leases.md)).

**Dependencies.** msgspec; why is in [decision 6](docs/decisions/0006-dependencies.md). Adding a
runtime dependency needs an ADR.
