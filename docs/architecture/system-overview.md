
# CeramETS System Architecture

## Overview
CeramETS is an AI-powered compliance platform designed to replace human consultants for the EU ETS (European Union Emissions Trading System) industries, specifically Ceramics and Tomato processing.

## Core Modules

### 1. Digital Twin Engine (`backend/infrastructure/models.py`)
- Maps physical assets (Kilns, Boilers) to `Installation` and `SourceStream` entities.
- Stores configuration history.

### 2. Calculation Engine (`backend/domain/calculations.py`)
- Configurable formula parser using AST.
- Traceable execution (Snapshot of inputs/factors).

### 3. Compliance Task Engine (`backend/domain/task_service.py`)
- Generates required tasks based on MRR/AVR rules.
- Manages deadlines for RE, ALC, and Verification.

### 4. RAG Advisory (`backend/domain/rag_service.py`)
- Vector database of EU Regulations (MRR, AVR, Directives).
- Provides cited answers to user queries.

### 5. Strategic Analyzer (`backend/domain/strategic_analysis.py`)
- ROI calculators for decarbonization.
- Anomaly detection for data quality.

### 6. Verifier Portal
- Secure, time-limited access for external auditors (APCER/SGS).

## Security
- Tenant isolation via `organization_id`.
- Audit logging for all critical actions.
- Role-based access control (RBAC).

## Tech Stack
- **Backend**: FastAPI (Python)
- **Database**: PostgreSQL + SQLAlchemy
- **AI**: Gemini Pro + Embeddings
- **Frontend**: React + Tailwind
