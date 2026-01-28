
# API Reference

## Authentication
- `POST /api/v1/auth/token`: Get JWT access token.

## Compliance
- `GET /api/v1/source-streams/{id}/form-definition`: Get JSON Schema for data entry.
- `POST /api/v1/emission-entries`: Submit monthly data.
- `GET /api/v1/tasks`: Get compliance checklist.

## Advisory & Strategy
- `POST /api/v1/advisory/chat`: RAG-enabled consultation.
- `POST /api/v1/advisory/analyze-fuel-switch`: ROI calculator.
- `POST /api/v1/advisory/detect-anomalies`: Statistical analysis.

## Verifier Portal
- `POST /api/v1/verifier/grant-access`: Create access link.
- `GET /api/v1/verifier/dashboard/{token}`: Public verifier view.
- `GET /api/v1/verifier/download-report/{token}`: Download official PDF.

## Documents
- `POST /api/v1/documents/upload`: Secure upload with hash check.
