
# Adding a New Sector

## 1. Define Sector Enum
Update `backend/infrastructure/models.py`:
```python
class SectorType(str, enum.Enum):
    CERAMIC = "CERAMIC"
    TOMATO = "TOMATO"
    GLASS = "GLASS" # New
```

## 2. Seed Data
Update `backend/infrastructure/seed_data.py`:
- Create `seed_glass_data()`.
- Define `SourceStream` templates (e.g., Soda Ash melting).
- Define `TaskDefinition` specific to glass (e.g., CEMS calibration).

## 3. Document Rules
Update `backend/domain/document_types.py`:
- Add specific document types (e.g., `ANALISE_CULLET`).
- Define validation rules (mandatory fields).

## 4. Frontend
- Update `ComplianceManager.tsx` to include the new sector in the switcher.
