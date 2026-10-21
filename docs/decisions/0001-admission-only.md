# 1. Decide who starts, not run the work

**Status:** Accepted

## Context

Loom, the first user, queues long-running agent work per domain in its own PostgreSQL tables and
claims it oldest first. Two users who each start ten pieces of work get ten for the first, then ten
for the second; there is no priority and no shared cap on how much runs at once or how fast it starts.

Fairness between tenants, priority and limits exist together only inside execution platforms —
[Hatchet](https://docs.hatchet.run/home/concurrency),
[Temporal](https://docs.temporal.io/develop/task-queue-priority-fairness),
[Inngest](https://inngest.com/platform/flow-control) — or paid editions such as
[BullMQ Pro](https://docs.bullmq.io/bullmq-pro/groups/rate-limiting). Python queues
([PgQueuer](https://github.com/janbjorge/pgqueuer), procrastinate, SAQ, arq, Celery,
[DBOS](https://docs.dbos.dev/python/reference/queues)) have priority or limits but no fairness
between tenants. Checked 2026-10-21.

## Decision

wicket is admission control only: it decides **which waiting ticket may start now**. It does not run
the work, retry it, store its result or keep its status; the caller's queue keeps all of that. The
limits it keeps are the caller's own capacity; a model provider's limits belong to the code that
calls the model.

## Alternatives

- **A full queue with smarter ordering.** It forces a task model, statuses and retries on every user,
  and in Loom it would replace every domain's queue.
- **Adopt a platform.** It adds a runtime that owns execution, against Loom's rule of no broker and
  no workflow engine.
- **Order `claim_next` by `ROW_NUMBER() OVER (PARTITION BY owner ORDER BY created_at)`.** It
  interleaves users in a few lines per domain, with no priority and no shared limits.

## Consequences

- wicket adds to any queue rather than replacing it; the caller keeps its own rows and links a ticket
  to one through the ticket's id.
- The caller submits a ticket when its user asks for the work, so wicket sees the whole backlog.
