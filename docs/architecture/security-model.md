
# Security & Compliance Model

## 1. Tenant Isolation
- **Strategy**: Row-Level Security logic at Application Layer.
- **Implementation**: Every API endpoint validates `current_user.organization_id` against the requested resource's `organization_id`.
- **Enforcement**: `TenantAccessError` raised on violation.

## 2. Verifier Access
- **Challenge**: Granting external auditors (APCER, SGS) access without full accounts.
- **Solution**: Capability URLs (Time-limited tokens).
- **Flow**: 
  1. Operator generates link for `installation_id` + `email`.
  2. Token stored in `VerifierAccess` table with `expires_at`.
  3. Verifier accesses `/dashboard/{token}`.
  4. Backend middleware validates token signature and expiration.

## 3. Audit Trails
- **Requirement**: Full traceability for EU ETS verification.
- **Implementation**: `AuditLog` table records:
  - WHO (User ID)
  - WHEN (Timestamp)
  - WHAT (Entity: EmissionEntry, Action: CREATE/UPDATE)
  - DETAILS (JSON diff of changes)
- **Immutability**: `EmissionEntry` records are locked after verification.

## 4. Regulatory Compliance
- **Data Retention**: 10 years (per MRR Article 66).
- **Privacy**: GDPR compliance for user data (minimal PII stored).
