import pytest
from datetime import datetime
from backend.domain.calculations import GenericCalculationEngine
from backend.infrastructure.database import Base, get_db
from backend.infrastructure.seed_data import seed_initial_data
from backend.infrastructure.models import Installation, SourceStream
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

# Test Database Setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_calc.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="module")
def db_session():
    """Create a fresh database and seed it with configuration data."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    
    # Seed Data (Org, Installation, Factors, Source Streams)
    seed_initial_data(db)
    
    yield db
    
    db.close()
    Base.metadata.drop_all(bind=engine)
    if os.path.exists("./test_calc.db"):
        os.remove("./test_calc.db")

def test_generic_combustion_calculation(db_session):
    """
    Test that the generic engine can calculate Natural Gas emissions
    by reading formulas and factors from the DB.
    """
    engine = GenericCalculationEngine(db_session)
    
    # 1. Get the Source Stream created by seed_data
    stream = db_session.query(SourceStream).filter(
        SourceStream.name == "Natural Gas Combustion Line 1"
    ).first()
    assert stream is not None
    
    # 2. Define Input (Activity Data = 1000 Nm3)
    input_data = {"activity_data": 1000.0}
    calc_date = datetime(2024, 6, 1)
    
    # 3. Run Calculation
    # Formula: activity * ncv * ef * of * 0.001
    # Expected: 1000 * 0.03854 * 56.1 * 1.0 * 0.001
    # = 2.162094
    
    result = engine.calculate(stream.id, input_data, calc_date)
    
    assert result.unit == "tCO2"
    assert result.value == 2.1621 # Rounded to 4 decimals
    assert result.factors_snapshot['ef'] == 56.1
    assert result.factors_snapshot['ncv'] == 0.03854

def test_missing_input_validation(db_session):
    """Test that the engine raises error if required inputs are missing."""
    engine = GenericCalculationEngine(db_session)
    stream = db_session.query(SourceStream).first()
    
    # Missing 'activity_data'
    input_data = {"wrong_field": 100.0}
    
    with pytest.raises(ValueError) as excinfo:
        engine.calculate(stream.id, input_data, datetime.now())
    
    assert "Missing required inputs" in str(excinfo.value)
