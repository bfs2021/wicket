# 3. Priority is a weighted sum of factors, and the highest wins

**Status:** Accepted

## Context

Different work needs different ways of judging what goes first: whose turn it is, a paid plan, a
nearer deadline, how long a ticket has waited. Two questions hide in "priority": how important a
ticket is, and how importance becomes a choice.

## Decision

- **A `Factor` scores every waiting ticket of a view in `0..1`** by one trait, all at once, so a
  factor that compares tickets does its work once per decision. Shipped: `FairShare()`,
  `Age(full_after)`, and `Fact(accessor)` for a trait of the caller's `facts`.
- **`Priority` is weighted factors,** as in [Slurm's multifactor
  priority](https://slurm.schedmd.com/priority_multifactor.html), and `first(view)` returns the
  ticket with the highest weighted sum; ties go to the earlier `submitted_at`, then the smaller id.
  An empty `Priority` is FIFO.
- **No ordering seam.** Fairness and favouring a user are both factors, so a second discipline would
  solve the same problems less predictably.
- **What a weight means:** a factor decides alone when its weight times the smallest step between its
  scores exceeds the sum of the other weights; the others only break its ties.
- **`Fact` trusts its value.** The caller keeps facts in range where they enter, such as with
  `msgspec.Meta(ge=0, le=1)`, so one bad ticket cannot fail every decision of the pool.
- **Pools do not nest.** Capacity is split between pools, as Kubernetes API Priority and Fairness
  gives each priority level its own seats.

## Alternatives

- **A pluggable ordering** (strict, weighted random). Dropped: with `Age` and `FairShare` in the
  score, the highest priority already gives fairness and no starvation, predictably.
- **Priority levels.** A `Fact` with a deciding weight gives the same precedence and composes with the
  other factors.

## Consequences

- A deciding `Fact` gives precedence, not a share: under a steady flow of high-tier work lower tiers
  wait.
- `Age` caps at `1` and cannot outweigh a heavier factor.
