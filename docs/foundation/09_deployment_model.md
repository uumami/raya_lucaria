# Deployment Model

Deployment is an adapter layer. It must not define the architecture.

## Supported Profiles

```text
same framework
     |
     +--> static only
     +--> local development
     +--> one-machine self-hosted
     +--> on-prem institution
     +--> free-tier managed services
     +--> paid cloud
```

## Static Only

Static-only deployment serves the course artifact as files. It is the baseline and must remain useful.

Good for:

- public course reading,
- durable access,
- zero-backend publishing,
- low-cost hosting.

## Local And One-Machine

The reference dynamic deployment should be able to run locally or on one server:

```text
reverse proxy
web app
API/core service
worker
Postgres
object storage or filesystem
backup job
optional realtime service
```

If this path does not work, the architecture is too vendor-shaped.

## Managed Providers

Free-tier and paid-cloud providers are convenience adapters. Docs must state:

- what the provider supplies,
- limits and costs,
- data ownership,
- migration path,
- self-hosted equivalent.

Examples may include Git hosting, static hosting, managed Postgres, object storage, serverless workers, auth providers, or realtime services. None are mandatory.

## Installation-Level Economics

One installation should serve many courses.

```text
monthly installation cost / active courses = rough cost per course
```

Costs belong to the deployment profile, not the course contract.
