# Ownership & Permissions

Raya Lucaria must keep authority visible. The same text, card, explanation, or note can mean different things depending on who created it, who can see it, and whether it has been reviewed.

## Authority Domains

```text
+-------------------+-------------------+-------------------------+
| Domain            | Owner             | Authority               |
+-------------------+-------------------+-------------------------+
| Official canon    | Course team       | Reviewed course truth   |
| Static artifact   | Course publisher  | Public read-only output |
| Personal work     | Student/user      | Private by default      |
| Shared course     | Course community  | Peer-visible            |
| Generated draft   | User or agent     | Not official            |
| Backend state     | Installation      | Sync/trust/realtime     |
| Accepted change   | Course team       | Official after review   |
+-------------------+-------------------+-------------------------+
```

## Review Boundary

Agents can generate. Students can save. Peers can share. Professors and delegated course staff approve canon.

```text
private note / generated card / suggested edit
                  |
                  v
            private draft
                  |
       +----------+----------+
       |                     |
       v                     v
 share with course     propose official change
       |                     |
       v                     v
 community space       review queue or PR
                             |
                             v
                       course team review
                             |
                             v
                      canonical source
```

## Permission Rules

- Personal work is private by default.
- Shared work is scoped to a course and visibility setting.
- Generated material is labeled as generated until reviewed.
- Official course material changes only through review.
- Agents inherit the authority of the authorizing user or role.
- Backend records are scoped by installation, course, user, role, and visibility.

## UI Responsibility

The UI must not blur authority. A student should be able to distinguish:

- official base card,
- platform-personalized card,
- student-created card,
- classmate-shared card,
- agent-generated draft,
- accepted official update.

Clear labels are part of the safety model.
