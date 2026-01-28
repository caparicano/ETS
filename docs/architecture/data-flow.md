
# Data Flow Architecture

## 1. Ingestion Layer
### PDF Parsing (TEGEH Permits)
1. **Input**: User uploads PDF permit via `WizardService`.
2. **Processing**: `TEGEHParser` extracts text using `pypdf`.
3. **AI Analysis**: Gemini Flash identifies equipment (Kilns, Boilers) and fuels.
4. **Storage**: Parsed structure stored in `WizardSession` context.

### Monthly Data Entry
1. **Input**: User enters activity data (e.g., Gas consumption in Nm³) via `DynamicEmissionForm`.
2. **Validation**: `InputFormDefinition` validates JSON Schema (min/max/types).
3. **Calculation**: `GenericCalculationEngine` executes configured formula.
4. **Persistence**: `EmissionEntry` stored with full calculation trace (inputs + factors).

## 2. Processing Layer
### Calculation Engine
- **Trigger**: New `EmissionEntry` or update.
- **Mechanism**: AST-based safe evaluation (`asteval`).
- **Audit**: Every calculation saves a snapshot of the Emission Factors used at that specific timestamp.

### RAG Advisory
1. **Query**: User asks question in `Consultation` component.
2. **Vector Search**: `RegulatoryLibraryService` finds relevant chunks (Cosine Similarity).
3. **Synthesis**: LLM combines chunks + Installation Context -> Response with Citations.

## 3. Reporting Layer
### APA Reports
1. **Aggregation**: `APAReportGenerator` sums `EmissionEntry` records by stream/year.
2. **Formatting**: `reportlab` generates PDF following APA official layout.
3. **Verification**: Verifier accesses read-only dashboard via `VerifierAccess` token.

## 4. Diagram
[User] -> [API Gateway] -> [Services] -> [PostgreSQL]
                            |
                            v
                       [Gemini AI]
