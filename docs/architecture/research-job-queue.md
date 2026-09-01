# Finance Research Job Queue

Status: schema baseline, 2026-08-31

Finance research work that must outlive an HTTP request will use
`finance.research_jobs`. The queue is tenant-scoped and stores the validated
command payload, not provider credentials or raw model prompts.

## Lifecycle

```text
queued -> processing -> succeeded
                    -> failed
```

Workers with `finance.research.worker` permission claim only eligible `queued`
jobs within their tenant, increment `attempts`, and set
`locked_at` and `locked_by`. A lease timeout can return abandoned `processing`
jobs to `queued`; the retry policy and maximum attempts belong to the worker
runbook, not to the domain model.

## Safety Rules

- `request_id` and operation are unique within a tenant.
- The payload must conform to the versioned Finance command contract before it
  is inserted.
- RLS prevents callers from reading or inserting another actor's jobs.
- Job payloads must exclude credentials, authorization headers, and raw model
  prompts.
- Completion still writes the existing research record and audit entry in the
  same Finance unit-of-work boundary.

The synchronous HTTP endpoint remains available for compatibility. The
asynchronous endpoint enqueues work, and the worker performs claim,
acknowledge, retry, and dead-letter operations against this table.
