# Security & Registration

Static sites, repositories, agents, and backends must not be trusted just because they claim a name or URL.

## Stable IDs

Core identities:

- `course_id`: stable course identity across repo renames and redeployments.
- `installation_id`: stable identity for a dynamic deployment.
- `artifact_id` or `course_version_id`: specific built version.
- `quantum_id`: stable identity for a learning quantum when path identity is not enough.

URLs and display names are metadata, not authority.

## Registration Flow

```text
course artifact
      |
      v
registration request
      |
      v
authorized maintainer approval
      |
      v
installation stores:
  course_id
  artifact verification
  allowed origins
  course team roles
  provider metadata
```

The backend must reject unregistered or mismatched claims.

## Trust Boundaries

```text
static artifact      public read path
browser              user-controlled environment
course repo          canonical reviewed source
installation/core    permissioned dynamic state
Git provider         review/history adapter
object storage       files/exports adapter
agent                delegated action
```

Agents inherit user authority. They do not receive extra trust.

## Auditability

Security-sensitive actions should leave an audit trail:

- course registration,
- role changes,
- canonical review decisions,
- deployment changes,
- provider connection changes,
- agent-authorized proposed changes.

Audit trails make authority visible and protect the commons.
