
from sqlalchemy import (
    Column, Integer, String, Boolean, ForeignKey, DateTime, Enum, JSON, Float, Text, Index, Date
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from .database import Base

# --- Enums ---
class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    EDITOR = "EDITOR"
    AUDITOR = "AUDITOR"

class SectorType(str, enum.Enum):
    CERAMIC = "CERAMIC"
    TOMATO = "TOMATO"

class DocStatus(str, enum.Enum):
    PENDING = "PENDING"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"
    LOCKED = "LOCKED"
    OCR_FAILED = "OCR_FAILED" # New status

class TaskStatus(str, enum.Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    OVERDUE = "OVERDUE"
    SKIPPED = "SKIPPED"

class RecurrenceType(str, enum.Enum):
    ONE_OFF = "ONE_OFF"
    ANNUAL = "ANNUAL"
    SEMI_ANNUAL = "SEMI_ANNUAL"
    QUARTERLY = "QUARTERLY"
    MONTHLY = "MONTHLY"

class WeekendRule(str, enum.Enum):
    SHIFT_FORWARD = "SHIFT_FORWARD"  # Move to Monday
    SHIFT_BACKWARD = "SHIFT_BACKWARD" # Move to Friday
    ALLOW = "ALLOW" # Keep on weekend

class WizardState(str, enum.Enum):
    UPLOAD_PERMIT = "UPLOAD_PERMIT"
    CONFIRM_EQUIPMENT = "CONFIRM_EQUIPMENT"
    FUEL_DETAILS = "FUEL_DETAILS"
    TIER_VALIDATION = "TIER_VALIDATION"
    PREVIEW_CONFIG = "PREVIEW_CONFIG"
    COMPLETED = "COMPLETED"

# --- Tenancy & Users ---

class Organization(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    vat_number = Column(String, unique=True, index=True)
    sector = Column(Enum(SectorType), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    users = relationship("User", back_populates="organization")
    installations = relationship("Installation", back_populates="organization")
    document_rules = relationship("DocumentValidationRule", back_populates="organization")

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.EDITOR)
    organization_id = Column(Integer, ForeignKey("organizations.id"))
    
    organization = relationship("Organization", back_populates="users")
    advisory_sessions = relationship("AdvisorySession", back_populates="user")
    generated_verifier_links = relationship("VerifierAccess", back_populates="created_by_user")

# --- Digital Asset Twin ---

class Installation(Base):
    __tablename__ = "installations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    permit_id = Column(String, unique=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"))
    monitoring_plan_config = Column(JSON, default={}) 
    
    organization = relationship("Organization", back_populates="installations")
    emissions = relationship("EmissionEntry", back_populates="installation")
    emission_factors = relationship("EmissionFactor", back_populates="installation")
    source_streams = relationship("SourceStream", back_populates="installation")
    tasks = relationship("ComplianceTask", back_populates="installation")
    verifier_access_links = relationship("VerifierAccess", back_populates="installation")

# --- Configuration & Generic Engine Tables ---

class EmissionFactor(Base):
    """Store configurable emission factors per installation."""
    __tablename__ = "emission_factors"
    
    id = Column(Integer, primary_key=True, index=True)
    installation_id = Column(Integer, ForeignKey("installations.id"), nullable=False)
    fuel_type = Column(String, nullable=False)  # "natural_gas", "biomass", "diesel"
    parameter_name = Column(String, nullable=False)  # "ncv_gj_nm3", "ef_kg_co2_gj", "oxidation_factor"
    value = Column(Float, nullable=False)
    unit = Column(String, nullable=False)
    tier = Column(Integer, nullable=False)  # 1, 2, or 3
    valid_from = Column(DateTime(timezone=True), nullable=False)
    valid_to = Column(DateTime(timezone=True), nullable=True)
    source = Column(String, nullable=False)  # "MRR 2024", "Lab Analysis #123"
    regulatory_reference = Column(String, nullable=True)  # "MRR Annex VI, Table 1"
    
    installation = relationship("Installation", back_populates="emission_factors")
    
    __table_args__ = (
        Index('ix_emission_factors_lookup', 'installation_id', 'fuel_type', 'parameter_name', 'valid_from'),
    )

class SourceStream(Base):
    """Define emission sources within an installation (replaces hardcoded sector logic)."""
    __tablename__ = "source_streams"
    
    id = Column(Integer, primary_key=True, index=True)
    installation_id = Column(Integer, ForeignKey("installations.id"), nullable=False)
    name = Column(String, nullable=False)  # "Natural Gas Combustion"
    category = Column(String, nullable=False)  # "combustion", "process"
    fuel_or_material = Column(String, nullable=True)  # "natural_gas", "clay"
    calculation_method = Column(String, nullable=False)  # "standard", "mass_balance"
    tier = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True)
    
    # Formula template stored as string (e.g., "activity * ncv * ef * of")
    formula_template = Column(String, nullable=False)
    
    # Required input fields as JSON (e.g., ["activity_data_nm3", "ncv_gj_nm3"])
    required_inputs = Column(JSON, nullable=False)
    
    installation = relationship("Installation", back_populates="source_streams")
    emission_entries = relationship("EmissionEntry", back_populates="source_stream")
    form_definition = relationship("InputFormDefinition", uselist=False, back_populates="source_stream")

class InputFormDefinition(Base):
    """
    Stores the JSON Schema for the UI to render forms dynamically.
    One-to-One with SourceStream.
    """
    __tablename__ = "input_form_definitions"

    id = Column(Integer, primary_key=True, index=True)
    source_stream_id = Column(Integer, ForeignKey("source_streams.id"), unique=True, nullable=False)
    json_schema = Column(JSON, nullable=False)
    ui_schema = Column(JSON, default={})
    version = Column(Integer, default=1)
    source_stream = relationship("SourceStream", back_populates="form_definition")

class DocumentValidationRule(Base):
    """Configurable document validation rules (replaces hardcoded APA_DOCUMENT_RULES)."""
    __tablename__ = "document_validation_rules"
    
    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)  # NULL = global rule
    document_type = Column(String, nullable=False)
    allowed_formats = Column(JSON, nullable=False)  # [".pdf", ".xml"]
    max_size_mb = Column(Integer, nullable=False)
    requires_digital_signature = Column(Boolean, default=False)
    mandatory_fields = Column(JSON, nullable=True)  # ["installation_id", "reporting_year"]
    must_contain_keywords = Column(JSON, nullable=True)  # For OCR validation
    
    organization = relationship("Organization", back_populates="document_rules")

# --- Task Engine ---

class TaskDefinition(Base):
    __tablename__ = "task_definitions"
    
    id = Column(Integer, primary_key=True, index=True)
    regulator = Column(String, nullable=False)
    task_code = Column(String, nullable=False, unique=True)
    title_pt = Column(String, nullable=False)
    title_en = Column(String)
    description_pt = Column(Text)
    sector_filter = Column(Enum(SectorType), nullable=True)
    recurrence_type = Column(Enum(RecurrenceType), default=RecurrenceType.ANNUAL)
    deadline_type = Column(String, default="fixed_date")
    deadline_month = Column(Integer, nullable=True)
    deadline_day = Column(Integer, nullable=True)
    deadline_offset_days = Column(Integer, default=0)
    weekend_rule = Column(Enum(WeekendRule), default=WeekendRule.SHIFT_FORWARD)
    priority = Column(Integer, default=5)
    depends_on_task_code = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    tasks = relationship("ComplianceTask", back_populates="definition")

class ComplianceTask(Base):
    __tablename__ = "compliance_tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    installation_id = Column(Integer, ForeignKey("installations.id"), nullable=False)
    definition_id = Column(Integer, ForeignKey("task_definitions.id"), nullable=False)
    reporting_year = Column(Integer, nullable=False)
    period_month = Column(Integer, nullable=True)
    due_date = Column(Date, nullable=False)
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    completed_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    title_override = Column(String, nullable=True)
    
    installation = relationship("Installation", back_populates="tasks")
    definition = relationship("TaskDefinition", back_populates="tasks")
    
    __table_args__ = (
        Index('ix_tasks_due_date', 'installation_id', 'due_date'),
        Index('ix_tasks_status', 'status', 'due_date'),
    )

# --- Phase 1.3 Wizard ---

class WizardSession(Base):
    """Stores the state of an ongoing AI interview."""
    __tablename__ = "wizard_sessions"

    id = Column(String, primary_key=True) # UUID
    organization_id = Column(Integer, ForeignKey("organizations.id"))
    state = Column(Enum(WizardState), default=WizardState.UPLOAD_PERMIT)
    context = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

# --- Phase 2: RAG & Advisory ---

class RegulatoryDocument(Base):
    """
    Registry of official texts (MRR, AVR, Portarias).
    """
    __tablename__ = "regulatory_documents"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False) # e.g. "Regulation (EU) 2018/2066"
    short_code = Column(String, unique=True) # e.g. "MRR_2018"
    doc_type = Column(String) # "EU Regulation", "Directive", "PT Law"
    publication_date = Column(Date)
    last_updated = Column(DateTime(timezone=True), server_default=func.now())
    
    chunks = relationship("RegulatoryChunk", back_populates="document", cascade="all, delete-orphan")

class RegulatoryChunk(Base):
    """
    Granular chunks of regulation for Vector Search.
    Ideally stores 'article_number' for citation.
    """
    __tablename__ = "regulatory_chunks"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("regulatory_documents.id"), nullable=False)
    article_reference = Column(String, nullable=False) # e.g. "Article 38(2)"
    content = Column(Text, nullable=False)
    embedding = Column(JSON) # Storing vector as JSON list [0.1, 0.2...] for portability
    
    document = relationship("RegulatoryDocument", back_populates="chunks")

class AdvisorySession(Base):
    """Chat history for the Consultant Module."""
    __tablename__ = "advisory_sessions"
    
    id = Column(String, primary_key=True) # UUID
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String)
    context_data = Column(JSON, default={}) # Stores active installation_id, sector, etc.
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User", back_populates="advisory_sessions")
    messages = relationship("AdvisoryMessage", back_populates="session", cascade="all, delete-orphan")

class AdvisoryMessage(Base):
    """Individual message in a consultation."""
    __tablename__ = "advisory_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, ForeignKey("advisory_sessions.id"))
    role = Column(String) # "user", "model", "system"
    content = Column(Text)
    citations = Column(JSON, default=[]) # List of citation objects
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    session = relationship("AdvisorySession", back_populates="messages")

# --- Phase 2: Verifier Portal ---

class VerifierAccess(Base):
    """Time-limited access tokens for external verifiers (APCER/SGS)."""
    __tablename__ = "verifier_access"
    
    token = Column(String, primary_key=True)
    installation_id = Column(Integer, ForeignKey("installations.id"), nullable=False)
    verifier_email = Column(String, nullable=False)
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_revoked = Column(Boolean, default=False)
    
    installation = relationship("Installation", back_populates="verifier_access_links")
    created_by_user = relationship("User", back_populates="generated_verifier_links")

# --- Evidence Vault & Ledger ---

class Document(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False) 
    file_hash = Column(String, nullable=False, index=True)
    document_type = Column(String, nullable=False) 
    reporting_year = Column(Integer, nullable=True)
    upload_date = Column(DateTime(timezone=True), server_default=func.now())
    locked_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(Enum(DocStatus), default=DocStatus.PENDING)
    version = Column(Integer, default=1)
    extracted_metadata = Column(JSON, default={})
    
    # New column for OCR results
    extracted_text = Column(Text, nullable=True)
    
    uploaded_by_id = Column(Integer, ForeignKey("users.id"))
    installation_id = Column(Integer, ForeignKey("installations.id"))

class EmissionEntry(Base):
    __tablename__ = "emission_entries"
    id = Column(Integer, primary_key=True, index=True)
    installation_id = Column(Integer, ForeignKey("installations.id"))
    source_stream_id = Column(Integer, ForeignKey("source_streams.id"), nullable=True)
    date_start = Column(DateTime, nullable=False)
    date_end = Column(DateTime, nullable=False)
    source_stream_name = Column(String, nullable=False)
    calculated_tco2 = Column(Float, nullable=False)
    calculation_trace = Column(JSON, nullable=False) 
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    installation = relationship("Installation", back_populates="emissions")
    source_stream = relationship("SourceStream", back_populates="emission_entries")

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, index=True)
    entity_type = Column(String, nullable=False)
    entity_id = Column(Integer, nullable=False)
    action = Column(String, nullable=False)
    changes = Column(JSON)
    user_id = Column(Integer, ForeignKey("users.id"))
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
