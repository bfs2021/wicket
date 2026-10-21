# 6. msgspec is the only runtime dependency of the core

**Status:** Accepted

## Context

A ticket's `facts` are the caller's typed payload, and every store must persist them. Values in the
core are immutable records.

## Decision

- **msgspec** for every value: frozen `Struct`s, and the encoding a store uses for `facts`, which the
  caller declares as a frozen `msgspec.Struct`.
- **The PostgreSQL store is an optional extra,** `wicket[postgres]`, so the core installs with
  msgspec alone. Its driver is chosen when the store is built, in its own decision.

## Alternatives

- **dataclasses.** No encoding or validation of their own; every store would write its own.
- **Pydantic.** Heavier, and mutable by default.

## Consequences

- A caller's facts must be a msgspec type.
- No logging or metrics library: observation is the caller's wrapper.
