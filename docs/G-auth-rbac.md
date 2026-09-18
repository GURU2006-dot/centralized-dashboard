# G. Authentication and RBAC

## 1. Goals

- Four demo roles working in minutes.
- Every mutating route checks role.
- Field officers only see assigned verifications / parcels.
- Officers scoped to `users.state_code` when set; admin unscoped.
- Audit who did what.

Not in MVP: OAuth/SSO, Aadhaar, refresh-token rotation, API keys for partners, per-permission bitmaps.

---

## 2. Authentication flow

```
LoginPage
  POST /api/auth/login { email, password }
        ↓
auth_service
  load user by email
  verify password (passlib bcrypt)
  reject if !is_active
        ↓
security.create_access_token({ sub: user.id, role: role.code, sv: password_epoch })
        ↓
200 { access_token, token_type, expires_in, user }
        ↓
AuthContext stores token in memory + sessionStorage
client.js attaches Authorization: Bearer
        ↓
deps.get_current_user
  decode JWT (jose/python-jose)
  load user; 401 if missing/disabled
        ↓
deps.require_roles(*codes)
  403 if user.role.code not in codes
```

Logout: client drops token; `POST /api/auth/logout` returns 204.

`GET /api/auth/me` hydrates UI on refresh.

---

## 3. JWT strategy

| Claim | Value |
|---|---|
| `sub` | user UUID |
| `role` | role code (convenience; **authorization still loads DB role**) |
| `iat` / `exp` | now / now+8h |
| `iss` | `nlamp-prototype` |

- Algorithm: **HS256**
- Secret: `JWT_SECRET` from env (`.env.example` has a dev-only string)
- Access token only. 8 hours matches a demo day.
- No server-side denylist (stateless). Disabling a user invalidates on next `get_current_user` DB check, not instantly for already-issued tokens — acceptable for prototype.
- Passwords: bcrypt, cost 12. Seeded demo passwords in `data/seed/users.csv` and README (e.g. `Demo@1234`) — **never production**.

CORS: `FRONTEND_ORIGIN` (Vite dev server). Credentials not needed (Bearer header, not cookies). CSRF therefore not applicable to JWT-in-header.

---

## 4. Authorization dependencies

`app/deps.py`:

| Dependency | Effect |
|---|---|
| `DbSession` | SQLAlchemy session |
| `CurrentUser` | required JWT |
| `require_roles("ADMIN", ...)` | 403 otherwise |
| `optional_user` | unused in MVP |

Scope helper `apply_geo_scope(query, user)`:

- `ADMIN` / `APPROVING_AUTHORITY`: no geo filter (authority is “national” in the prototype unless `state_code` set).
- `ACQUISITION_OFFICER` with `state_code`: filter projects/parcels to that state (and district if set).
- `FIELD_OFFICER`: parcels via `field_verifications.assigned_to == user.id` (and those parcels’ cases).

Object-level: field submit allowed iff `assigned_to == current_user.id` (or admin). Proposal approve iff role is `APPROVING_AUTHORITY`.

---

## 5. Permission matrix

Legend: R read, W create/update, X action, — none.

| Capability | ADMIN | ACQ OFFICER | APPROVER | FIELD |
|---|---|---|---|---|
| National dashboard | R | R (scoped) | R | R (limited KPIs ok) |
| Manage users | W | — | — | — |
| Manage projects | W | W | R | — |
| Configure dashboard presets | W (P2) | — | — | — |
| View audit logs | R | — | — | — |
| Create / submit proposals | — | X | — | — |
| Verify proposals | — | X | X | — |
| Approve / reject proposals | — | — | X | — |
| Manage parcels / documents | W | W | R | photo upload on assignment |
| Update acquisition workflow | X (override) | X | X (to APPROVAL only) | — |
| Track compensation / R&R / possession | R | W | R | — |
| View alerts | R all | R own | R own | R own |
| Evaluate alert rules | X | — | — | — |
| View assigned parcels | R all | R scoped | R | R assigned |
| Field verification submit / GPS / photo | — | — | — | X assigned |
| ML predict | X | X | X | — |
| Integration lookup | X | X | — | — |
| Reports | R | R | R | — |

This matches §5 of the spec. Extra “configure dashboards” is admin-only and P2.

---

## 6. Demo users (seed)

| Email | Role | Scope |
|---|---|---|
| `admin@demo.local` | ADMIN | national |
| `officer@demo.local` | ACQUISITION_OFFICER | Telangana |
| `approver@demo.local` | APPROVING_AUTHORITY | national |
| `field@demo.local` | FIELD_OFFICER | assigned ~8 parcels in a TG district |

Password documented in README. Login page lists them.

---

## 7. Middleware / cross-cutting

Order in `main.py`:

1. CORS
2. Request ID + access log
3. Routers (auth deps per-route, not global — login is public)
4. Exception handlers → error envelope
5. After successful mutating service calls: `audit_service.record(...)` **inside the service**, not a magic middleware guessing semantics.

Audit actions (minimum):  
`PROPOSAL_SUBMITTED`, `PROPOSAL_APPROVED`, `PROPOSAL_REJECTED`, `PARCEL_UPDATED`, `DOCUMENT_UPLOADED`, `DOCUMENT_VERIFIED`, `COMPENSATION_UPDATED`, `FIELD_VERIFICATION_SUBMITTED`, `WORKFLOW_STAGE_CHANGED`, `USER_ROLE_CHANGED`, `USER_UPDATED`, `PROJECT_CREATED`, `PROJECT_UPDATED`.

---

## 8. Frontend enforcement

`ProtectedRoute roles={['ADMIN']}` hides `/admin`.  
Sidebar filters by `user.role`.  

**UI hiding is not security.** API still returns 403. Frontend maps 401 → login, 403 → “Not permitted” toast.
