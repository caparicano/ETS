
# Testing Strategy

## 1. Unit Tests (`backend/tests/`)
- **Calculations**: Verify `GenericCalculationEngine` against Excel formulas from MRR Guidance.
- **RAG**: Mock vector search to ensure prompt construction is correct.
- **Tasks**: Verify deadline logic (leap years, weekends).

## 2. Integration Tests
- **Full Flow**: `test_complete_consultant_workflow.py` simulates a full year.
- **PDF Parsing**: Test with anonymized real TEGEH permits.

## 3. Regulatory Validation
- **Golden Data**: We use a set of known inputs/outputs from APA guidance examples to verify the engine's accuracy.
- **Security**: SQL injection attempts via formula engine (handled by `asteval`).

## 4. Running Tests
```bash
pytest backend/tests/
```
