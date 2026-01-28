
import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.domain.calculations import GenericCalculationEngine
from backend.infrastructure.database import Base
from backend.infrastructure.models import SourceStream, EmissionFactor, Installation, Organization, SectorType

# Setup In-Memory DB for logic testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)

def seed_mrr_scenario(db: Session, installation_id: int):
    """
    Seeds the DB with factors from Commission Regulation (EU) 2018/2066
    Annex VI - Default Emission Factors
    """
    # 1. Natural Gas Factors (Annex VI)
    factors = [
        {"p": "ncv", "v": 0.048, "u": "TJ/t"}, # Using TJ/t for mass balance example or GJ/Nm3 for standard
        {"p": "ef", "v": 56.1, "u": "tCO2/TJ"},
        {"p": "of", "v": 1.0, "u": "fraction"}
    ]
    for f in factors:
        db.add(EmissionFactor(
            installation_id=installation_id,
            fuel_type="natural_gas",
            parameter_name=f["p"],
            value=f["v"],
            unit=f["u"],
            tier=1,
            valid_from=datetime(2020,1,1),
            source="MRR 2018/2066 Annex VI"
        ))
    db.commit()

def test_mrr_standard_combustion_tier1(db_session):
    """
    REGULATORY VALIDATION TEST #1
    
    Scenario: Standard Combustion of Natural Gas (Tier 1)
    Reference: Guidance Document 1 (General Guidance), Example 1
    
    Input:
    - Activity Data: 50,000 Nm3
    - NCV: 0.038 GJ/Nm3 (Assumed Country Specific)
    - EF: 56.1 kgCO2/GJ (IPCC/MRR Default)
    - OF: 1.0 (Tier 1)
    
    Formula: Activity * NCV * EF * OF * 0.001 (conversion to tonnes)
    Expected: 50,000 * 0.038 * 56.1 * 1.0 * 0.001 = 106.59 tCO2
    """
    # Setup Infrastructure
    org = Organization(name="Test Org", vat_number="123", sector=SectorType.CERAMIC)
    db_session.add(org)
    db_session.commit()
    inst = Installation(name="Test Inst", permit_id="123", organization_id=org.id)
    db_session.add(inst)
    db_session.commit()
    
    # Setup Specific Factors for this test
    factors = [
        ("ncv", 0.038, "GJ/Nm3"),
        ("ef", 56.1, "kgCO2/GJ"),
        ("of", 1.0, "fraction")
    ]
    for name, val, unit in factors:
        db_session.add(EmissionFactor(
            installation_id=inst.id,
            fuel_type="natural_gas",
            parameter_name=name,
            value=val,
            unit=unit,
            tier=1,
            valid_from=datetime(2023,1,1),
            source="Test Scenario"
        ))
    
    # Setup Source Stream
    stream = SourceStream(
        installation_id=inst.id,
        name="Boiler 1",
        category="combustion",
        fuel_or_material="natural_gas",
        calculation_method="standard",
        tier=1,
        formula_template="activity * ncv * ef * of * 0.001",
        required_inputs=["activity"]
    )
    db_session.add(stream)
    db_session.commit()
    
    # Execute
    engine_svc = GenericCalculationEngine(db_session)
    result = engine_svc.calculate(
        source_stream_id=stream.id,
        input_data={"activity": 50000.0},
        calculation_date=datetime(2024,1,1)
    )
    
    # Assert
    assert result.value == 106.59
    assert result.unit == "tCO2"
    assert result.factors_snapshot["ef"] == 56.1

def test_security_injection_attempt(db_session):
    """
    SECURITY TEST #1
    Ensure malicious formulas cannot execute arbitrary code.
    """
    # Setup minimal valid stream
    org = Organization(name="Hacker Org", vat_number="666", sector=SectorType.CERAMIC)
    db_session.add(org)
    db_session.commit()
    inst = Installation(name="Hacker Inst", permit_id="666", organization_id=org.id)
    db_session.add(inst)
    db_session.commit()
    
    stream = SourceStream(
        installation_id=inst.id,
        name="Malicious Stream",
        category="combustion",
        fuel_or_material="magic",
        calculation_method="standard",
        tier=1,
        # Attempt to import OS and list directories
        formula_template="__import__('os').listdir('.')",
        required_inputs=["dummy"]
    )
    db_session.add(stream)
    db_session.commit()
    
    engine_svc = GenericCalculationEngine(db_session)
    
    # Assert that it fails safely
    with pytest.raises(ValueError) as excinfo:
        engine_svc.calculate(stream.id, {"dummy": 1}, datetime.now())
    
    # The error should come from asteval refusing the syntax or the function
    assert "Calculation Error" in str(excinfo.value) or "NameError" in str(excinfo.value)
