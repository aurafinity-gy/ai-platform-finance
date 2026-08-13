# ADR-FIN003: Finance Runtime Uses Postgres Unit Of Work And JWT Request Context

- Status: accepted
- Date: 2026-08-13

## Context

The initial Finance implementation used an in-memory bootstrap to keep the
first API and application slices easy to exercise in tests. That was helpful
for proving the Finance boundary, but it is not the right production shape for
a platform that needs durable research records, idempotent command handling,
audit history, and tenant-scoped authorization.

Finance also needs a real request context provider. Header-only context is
sufficient for local scaffolding, but production traffic should derive actor
identity from a signed bearer token and should not trust the caller to supply
its own tenant or role claims.

The Finance bounded context now has the first vertical slice from ADR-FIN002:
paper-trading research and decision workflows. That slice needs the same
runtime qualities a real desk would expect:

- persisted research records;
- idempotent command execution;
- tenant and actor authorization;
- audit entries for material workflow actions; and
- a composition root that can be deployed independently.

## Decision

Finance will use a database-backed unit of work for its production runtime and
a JWT-based request context provider for authenticated requests.

The finance runtime composition root will:

- create a Postgres-backed `FinanceUnitOfWorkFactory`;
- resolve `RequestContext` from a signed bearer token;
- use the token subject as the actor identity;
- use the tenant claim or tenant header selected by the runtime policy;
- apply idempotency and audit storage inside the Finance boundary; and
- keep the in-memory bootstrap only for tests and local wiring exercises.

Finance will keep the application layer abstracted behind ports so the
workflow code remains persistence-agnostic. The runtime may swap transport and
infrastructure adapters, but the command behavior stays inside the application
and domain layers.

The concrete Finance package tree will follow this shape:

```text
ai-platform-finance/
  applications/
    finance/
      domain/
      application/
      agents/
      api/
      persistence/
  services/
    api-fastapi/
    worker/
  contracts/
  docs/
    architecture/
    decisions/
  tests/
```

## Scope

This decision applies to:

- the Finance HTTP runtime;
- the Finance worker/runtime composition root;
- Finance-owned persistence adapters;
- Finance authentication and request-context resolution; and
- Finance command execution paths that require idempotency or audit trails.

## Explicit Non-Goals

- building a shared authentication implementation for all platform domains;
- using the database as a shared cross-domain integration surface;
- moving generic agent runtime code into Finance; or
- requiring the production runtime to depend on the in-memory bootstrap.

## Consequences

- Finance can persist research and decision history in a durable store.
- Command replays can be handled safely through idempotency records.
- Request authorization is derived from authenticated identity rather than
  caller-supplied demo headers.
- Tests can still use in-memory adapters, but production wiring is now explicit
  and separate.
- Future Finance capabilities can add more repositories and policies without
  changing the runtime contract shape.

## Follow-Up Work

1. Add migration scripts for the Finance and platform audit tables.
2. Add runtime health checks that verify the database and auth dependencies.
3. Add documentation for required deployment environment variables.
4. Extend the Finance worker flow to use the same unit of work factory.

