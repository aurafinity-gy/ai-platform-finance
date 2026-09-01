# Finance Application Definition

Use this file as the local entry point for defining a Finance application.
It should stay thin and point back to the shared handbook starter, then capture
only Finance-specific application choices.

Start here:

- [Shared application definition starter](../../../ai-platform-handbook/volume-03-applications/templates.md#application-definition-starter)
- [Finance application definition example](../../../ai-platform-handbook/volume-03-applications/application-definition-finance-example.md)

Capture in this repo:

- Application purpose and users
- Finance workflows and boundaries
- Foundation capabilities used
- Runtime configuration and secrets
- Data ownership, migrations, and rollback
- Release, smoke test, and observability notes

## MVP Application Slice

The first deployable Finance application slice is intentionally narrow:

- authenticate an operator through Foundation Auth;
- preserve the authenticated actor and tenant scope at the Finance boundary;
- submit a Finance research request with an idempotency key;
- enqueue the request for the Finance worker;
- expose live and ready health checks;
- persist the request, result, audit entry, and job state in Postgres.

The application does not yet place trades, connect to external market-data or
broker providers, or enable autonomous analyst debate. Those capabilities are
future releases and must be introduced behind versioned contracts, feature
flags, and explicit approval controls.

## Current Composition

The MVP is composed from:

- Foundation Auth and shared tenant/membership tables;
- `services/api-fastapi` as the Finance HTTP runtime;
- `services/worker` as the asynchronous Finance job worker;
- `applications/finance` for the Finance use-case and workflow contracts;
- the Foundation web surface and its `/finance` route as the public application shell;
- the shared private Docker network for service-to-service traffic.

The staging acceptance path is:

```text
browser -> Foundation web -> Foundation Auth
                       -> private Finance API -> Postgres / Finance worker
```

The Finance API is not exposed directly to the public internet. Any future
public route must be added as an explicitly reviewed application boundary.

## MVP Exit Criteria

- [x] Public HTTPS application shell is reachable.
- [x] Foundation Auth is available in the shared staging environment.
- [x] Finance API uses Postgres and JWT-derived request context.
- [x] Finance worker is running on the shared private network.
- [x] Finance health, readiness, tenant, audit, and idempotency checks pass.
- [x] The first Finance research-intake UI journey is implemented.
- [x] The authenticated browser journey is accepted with the approved staging operator.
- [ ] Production release approval is recorded for the product application.
