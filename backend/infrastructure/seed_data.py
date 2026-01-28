
import json
from sqlalchemy.orm import Session
from datetime import datetime
from .models import (
    EmissionFactor, SourceStream, Installation, Organization, 
    SectorType, DocumentValidationRule, InputFormDefinition,
    TaskDefinition, RecurrenceType, WeekendRule
)

def seed_apa_task_definitions(db: Session):
    """Seed comprehensive APA Portugal compliance tasks."""
    
    tasks = [
        # --- GENERAL / CERAMIC TASKS ---
        TaskDefinition(
            regulator="APA_PT",
            task_code="prepare_re_draft",
            title_pt="Preparar rascunho do Relatório de Emissões",
            title_en="Prepare Emissions Report draft",
            description_pt="Compilar todos os dados de emissões do ano e preparar rascunho do RE para envio ao verificador.",
            sector_filter=None,
            recurrence_type=RecurrenceType.ANNUAL,
            deadline_type="fixed_date",
            deadline_month=2,
            deadline_day=15,
            priority=2
        ),
        TaskDefinition(
            regulator="APA_PT",
            task_code="obtain_verification",
            title_pt="Obter Parecer de Verificação",
            title_en="Obtain Verification Opinion",
            description_pt="Contratar verificador acreditado (APCER, SGS, AENOR) e obter parecer positivo.",
            recurrence_type=RecurrenceType.ANNUAL,
            deadline_type="fixed_date",
            deadline_month=3,
            deadline_day=15,
            priority=1,
            depends_on_task_code="prepare_re_draft"
        ),
        TaskDefinition(
            regulator="APA_PT",
            task_code="submit_re_siliamb",
            title_pt="Submeter Relatório de Emissões via SILiAmb",
            title_en="Submit Emissions Report via SILiAmb",
            description_pt="Submissão oficial do RE através da plataforma SILiAmb da APA. Requer Parecer de Verificação positivo.",
            recurrence_type=RecurrenceType.ANNUAL,
            deadline_type="fixed_date",
            deadline_month=3,
            deadline_day=31,
            weekend_rule=WeekendRule.SHIFT_FORWARD,
            priority=1,
            depends_on_task_code="obtain_verification"
        ),
        TaskDefinition(
            regulator="APA_PT",
            task_code="rple_surrender",
            title_pt="Entrega de Licenças de Emissão (RPLE)",
            title_en="Surrender Emission Allowances (RPLE)",
            description_pt="Entrega de licenças correspondentes às emissões verificadas através do Registo Português de Licenças de Emissão (RPLE).",
            recurrence_type=RecurrenceType.ANNUAL,
            deadline_type="fixed_date",
            deadline_month=4,
            deadline_day=30,
            priority=1,
            depends_on_task_code="submit_re_siliamb"
        ),
        TaskDefinition(
            regulator="APA_PT",
            task_code="submit_alc",
            title_pt="Submeter Relatório de Nível de Atividade (ALC)",
            title_en="Submit Activity Level Report (ALC)",
            description_pt="Relatório de produção para ajuste de alocação gratuita. Obrigatório se produção variar >15%.",
            recurrence_type=RecurrenceType.ANNUAL,
            deadline_type="fixed_date",
            deadline_month=3,
            deadline_day=31,
            priority=2
        ),
        TaskDefinition(
            regulator="APA_PT",
            task_code="submit_improvement_plan",
            title_pt="Submeter Relatório de Melhoria",
            title_en="Submit Improvement Report",
            description_pt="Plano de melhoria se verificador encontrou não-conformidades ou se Tier atual não é o mais elevado tecnicamente possível.",
            recurrence_type=RecurrenceType.ANNUAL,
            deadline_type="fixed_date",
            deadline_month=6,
            deadline_day=30,
            priority=3,
            depends_on_task_code="obtain_verification"
        ),
        TaskDefinition(
            regulator="INTERNAL",
            task_code="enter_monthly_data",
            title_pt="Inserir Dados Mensais de Consumo",
            title_en="Enter Monthly Consumption Data",
            description_pt="Registar consumos de combustível e dados de produção do mês.",
            recurrence_type=RecurrenceType.MONTHLY,
            deadline_type="fixed_date",
            deadline_day=15,  
            priority=3
        ),
        TaskDefinition(
            regulator="INTERNAL",
            task_code="clay_lab_analysis",
            title_pt="Análise Laboratorial de Carbonatos (Trimestral)",
            title_en="Quarterly Carbonate Lab Analysis",
            description_pt="Enviar amostra de argila para laboratório acreditado ISO 17025 para análise de teor de CaCO3.",
            sector_filter=SectorType.CERAMIC,
            recurrence_type=RecurrenceType.QUARTERLY,
            deadline_type="fixed_date",
            deadline_day=30,
            priority=2
        ),

        # --- TOMATO / AGRI-FOOD TASKS ---
        TaskDefinition(
            regulator="APA_PT",
            task_code="pre_campaign_calibration",
            title_pt="Calibração Pré-Campanha (Equipamentos)",
            title_en="Pre-Campaign Equipment Calibration",
            description_pt="Calibrar contadores de vapor e gás antes do início da campanha de tomate (julho).",
            sector_filter=SectorType.TOMATO,
            recurrence_type=RecurrenceType.ANNUAL,
            deadline_type="fixed_date",
            deadline_month=6,  # June
            deadline_day=30,
            priority=2
        ),
        TaskDefinition(
            regulator="APA_PT",
            task_code="campaign_monthly_data",
            title_pt="Inserir Dados Mensais da Campanha",
            title_en="Enter Campaign Monthly Data",
            description_pt="Registar consumos de gás, biomassa e produção durante período de campanha (jul-out).",
            sector_filter=SectorType.TOMATO,
            recurrence_type=RecurrenceType.MONTHLY,
            deadline_type="fixed_date",
            deadline_day=15,
            priority=3
        ),
        TaskDefinition(
            regulator="APA_PT",
            task_code="post_campaign_reconciliation",
            title_pt="Reconciliação Pós-Campanha",
            title_en="Post-Campaign Reconciliation",
            description_pt="Reconciliar dados de emissões da campanha e preparar para verificação.",
            sector_filter=SectorType.TOMATO,
            recurrence_type=RecurrenceType.ANNUAL,
            deadline_type="fixed_date",
            deadline_month=11,  # November
            deadline_day=30,
            priority=2
        ),
        TaskDefinition(
            regulator="APA_PT",
            task_code="biomass_sustainability_report",
            title_pt="Relatório de Sustentabilidade da Biomassa",
            title_en="Biomass Sustainability Report",
            description_pt="Documentar critérios RED II para zero-rating de biomassa (resíduos de tomate).",
            sector_filter=SectorType.TOMATO,
            recurrence_type=RecurrenceType.ANNUAL,
            deadline_type="fixed_date",
            deadline_month=3,
            deadline_day=15,
            priority=2
        )
    ]
    
    for task in tasks:
        exists = db.query(TaskDefinition).filter_by(task_code=task.task_code).first()
        if not exists:
            db.add(task)
    db.commit()

def seed_ceramic_data(db: Session, installation_id: int):
    """Seed Ceramic industry specific configuration (Kilns, Carbonates)."""
    
    # 1. Source Streams
    ng_stream = SourceStream(
        installation_id=installation_id,
        name="Natural Gas Combustion - Tunnel Kiln",
        category="combustion",
        fuel_or_material="natural_gas",
        calculation_method="standard",
        tier=2,
        formula_template="activity_data_nm3 * ncv_gj_nm3 * ef_kg_co2_gj * oxidation_factor * 0.001",
        required_inputs=["activity_data_nm3"]
    )
    
    clay_stream = SourceStream(
        installation_id=installation_id,
        name="Process Emissions - Clay Carbonates",
        category="process",
        fuel_or_material="clay",
        calculation_method="mass_balance",
        tier=2,
        formula_template="clay_mass_tonnes * (carbonate_pct/100) * (44.0/100.0) * caco3_ratio",
        required_inputs=["clay_mass_tonnes", "carbonate_pct"]
    )
    
    for s in [ng_stream, clay_stream]:
        exists = db.query(SourceStream).filter_by(installation_id=installation_id, name=s.name).first()
        if not exists:
            db.add(s)
            db.commit()
            db.refresh(s)
            
            if s.fuel_or_material == "natural_gas":
                form = InputFormDefinition(
                    source_stream_id=s.id,
                    json_schema={
                        "type": "object",
                        "title": "Natural Gas Consumption",
                        "properties": {
                            "activity_data_nm3": {"type": "number", "title": "Consumo de Gás Natural (Nm³)", "unit": "Nm³"}
                        },
                        "required": ["activity_data_nm3"]
                    }
                )
                db.add(form)
            elif s.fuel_or_material == "clay":
                form = InputFormDefinition(
                    source_stream_id=s.id,
                    json_schema={
                        "type": "object",
                        "title": "Clay Consumption & Analysis",
                        "properties": {
                            "clay_mass_tonnes": {"type": "number", "title": "Massa de Argila (t)"},
                            "carbonate_pct": {"type": "number", "title": "Teor de CaCO3 (%)"}
                        },
                        "required": ["clay_mass_tonnes", "carbonate_pct"]
                    }
                )
                db.add(form)

    # 2. Emission Factors
    factors = [
        EmissionFactor(
            installation_id=installation_id,
            fuel_type="natural_gas",
            parameter_name="ncv_gj_nm3",
            value=0.03854,
            unit="GJ/Nm³",
            tier=1,
            source="MRR Annex VI",
            regulatory_reference="Commission Regulation (EU) 2018/2066",
            valid_from=datetime(2024, 1, 1)
        ),
        EmissionFactor(
            installation_id=installation_id,
            fuel_type="natural_gas",
            parameter_name="ef_kg_co2_gj",
            value=56.1,
            unit="kg CO2/GJ",
            tier=1,
            source="MRR Annex VI",
            regulatory_reference="Commission Regulation (EU) 2018/2066",
            valid_from=datetime(2024, 1, 1)
        ),
        EmissionFactor(
            installation_id=installation_id,
            fuel_type="natural_gas",
            parameter_name="oxidation_factor",
            value=1.0,
            unit="fraction",
            tier=1,
            source="MRR Default",
            regulatory_reference="Commission Regulation (EU) 2018/2066",
            valid_from=datetime(2024, 1, 1)
        ),
        EmissionFactor(
            installation_id=installation_id,
            fuel_type="clay",
            parameter_name="caco3_ratio",
            value=0.6,
            unit="dimensionless",
            tier=2,
            source="Industry average",
            regulatory_reference="MRR Annex II",
            valid_from=datetime(2024, 1, 1)
        )
    ]
    
    for f in factors:
        exists = db.query(EmissionFactor).filter_by(
            installation_id=installation_id, 
            fuel_type=f.fuel_type, 
            parameter_name=f.parameter_name
        ).first()
        if not exists:
            db.add(f)
    db.commit()

def seed_tomato_data(db: Session):
    """Seed Tomato / Agri-food specific configuration."""
    
    # Ensure Org and Inst exist for Tomato
    org = db.query(Organization).filter_by(vat_number="PT500999888").first()
    if not org:
        org = Organization(name="Sugal Tomato Processors", vat_number="PT500999888", sector=SectorType.TOMATO)
        db.add(org)
        db.commit()
    
    inst = db.query(Installation).filter_by(permit_id="TEGEH-2024-TOMATO").first()
    if not inst:
        inst = Installation(name="Benavente Plant", permit_id="TEGEH-2024-TOMATO", organization_id=org.id)
        db.add(inst)
        db.commit()
    
    installation_id = inst.id

    # Source Streams
    streams = [
        SourceStream(
            installation_id=installation_id,
            name="Natural Gas Combustion - Steam Boiler",
            category="combustion",
            fuel_or_material="natural_gas",
            calculation_method="standard",
            tier=2,
            formula_template="activity_data_nm3 * ncv_gj_nm3 * ef_kg_co2_gj * oxidation_factor * 0.001",
            required_inputs=["activity_data_nm3", "campaign_active"]
        ),
        SourceStream(
            installation_id=installation_id,
            name="Biomass Combustion - Tomato Waste",
            category="combustion",
            fuel_or_material="biomass",
            calculation_method="standard",
            tier=2,
            formula_template="biomass_mass_tonnes * ncv_gj_tonne * ef_kg_co2_gj * 0.001", # Zero rated logic usually involves EF=0
            required_inputs=["biomass_mass_tonnes", "sustainability_cert_id"]
        ),
        SourceStream(
            installation_id=installation_id,
            name="CHP Unit - Natural Gas",
            category="combustion",
            fuel_or_material="natural_gas",
            calculation_method="standard",
            tier=2,
            formula_template="activity_data_nm3 * ncv_gj_nm3 * ef_kg_co2_gj * oxidation_factor * 0.001",
            required_inputs=["activity_data_nm3", "electrical_efficiency_pct", "thermal_efficiency_pct"]
        )
    ]

    for s in streams:
        exists = db.query(SourceStream).filter_by(installation_id=installation_id, name=s.name).first()
        if not exists:
            db.add(s)
            db.commit()
            db.refresh(s)
            
            # Forms
            schema = {}
            if "Steam Boiler" in s.name:
                schema = {
                    "type": "object",
                    "title": "Consumo Mensal de Gás (Caldeira)",
                    "properties": {
                        "activity_data_nm3": {
                            "type": "number",
                            "title": "Consumo de Gás Natural (Nm³)",
                            "description": "Leitura do contador da caldeira",
                            "minimum": 0
                        },
                        "campaign_active": {
                            "type": "boolean",
                            "title": "Campanha Ativa?",
                            "description": "Marcar se está em período de campanha (jul-out)"
                        }
                    },
                    "required": ["activity_data_nm3", "campaign_active"]
                }
            elif "Biomass" in s.name:
                schema = {
                    "type": "object",
                    "title": "Consumo de Biomassa (Resíduos de Tomate)",
                    "properties": {
                        "biomass_mass_tonnes": {
                            "type": "number",
                            "title": "Massa de Biomassa (Toneladas)",
                            "description": "Resíduos de tomate queimados",
                            "minimum": 0
                        },
                        "sustainability_cert_id": {
                            "type": "string",
                            "title": "ID Certificado Sustentabilidade",
                            "description": "Referência do certificado RED II"
                        }
                    },
                    "required": ["biomass_mass_tonnes", "sustainability_cert_id"]
                }
            elif "CHP" in s.name:
                schema = {
                    "type": "object",
                    "title": "CHP Cogeneration Data",
                    "properties": {
                        "activity_data_nm3": {"type": "number", "title": "Consumo de Gás (Nm³)"},
                        "electrical_efficiency_pct": {"type": "number", "title": "Eficiência Elétrica (%)"},
                        "thermal_efficiency_pct": {"type": "number", "title": "Eficiência Térmica (%)"}
                    },
                    "required": ["activity_data_nm3"]
                }
            
            db.add(InputFormDefinition(source_stream_id=s.id, json_schema=schema))
            
    # Emission Factors
    factors = [
        # Biomass
        EmissionFactor(
            installation_id=installation_id,
            fuel_type="biomass",
            parameter_name="ncv_gj_tonne",
            value=4.5,
            unit="GJ/tonne",
            tier=2,
            source="Industry measurement - tomato processing waste",
            regulatory_reference="MRR Annex VI, Section 2.4 - Biomass",
            valid_from=datetime(2024, 1, 1)
        ),
        EmissionFactor(
            installation_id=installation_id,
            fuel_type="biomass",
            parameter_name="ef_kg_co2_gj",
            value=0.0,
            unit="kg CO2/GJ",
            tier=2,
            source="RED II Directive - sustainable biomass",
            regulatory_reference="Directive (EU) 2018/2001, Article 29",
            valid_from=datetime(2024, 1, 1)
        ),
        # Natural Gas (Copying standard ones for this new installation)
        EmissionFactor(
            installation_id=installation_id,
            fuel_type="natural_gas",
            parameter_name="ncv_gj_nm3",
            value=0.03854,
            unit="GJ/Nm³",
            tier=1,
            source="MRR Annex VI",
            regulatory_reference="Commission Regulation (EU) 2018/2066",
            valid_from=datetime(2024, 1, 1)
        ),
        EmissionFactor(
            installation_id=installation_id,
            fuel_type="natural_gas",
            parameter_name="ef_kg_co2_gj",
            value=56.1,
            unit="kg CO2/GJ",
            tier=1,
            source="MRR Annex VI",
            regulatory_reference="Commission Regulation (EU) 2018/2066",
            valid_from=datetime(2024, 1, 1)
        ),
        EmissionFactor(
            installation_id=installation_id,
            fuel_type="natural_gas",
            parameter_name="oxidation_factor",
            value=1.0,
            unit="fraction",
            tier=1,
            source="MRR Default",
            regulatory_reference="Commission Regulation (EU) 2018/2066",
            valid_from=datetime(2024, 1, 1)
        )
    ]
    
    for f in factors:
        exists = db.query(EmissionFactor).filter_by(
            installation_id=installation_id, 
            fuel_type=f.fuel_type, 
            parameter_name=f.parameter_name
        ).first()
        if not exists:
            db.add(f)
            
    db.commit()

def seed_document_rules(db: Session):
    """Seed validation rules for Ceramic and Tomato documents."""
    rules = [
        # Ceramic
        DocumentValidationRule(
            document_type="analise_carbonatos_argila",
            allowed_formats=[".pdf"],
            max_size_mb=5,
            requires_digital_signature=False,
            mandatory_fields=["caco3_percentage", "sample_id", "analysis_date", "lab_name"],
            must_contain_keywords=["ISO 17025", "CaCO3", "MgCO3"]
        ),
        DocumentValidationRule(
            document_type="certificado_calibracao_balanca",
            allowed_formats=[".pdf"],
            max_size_mb=3,
            requires_digital_signature=False,
            mandatory_fields=["calibration_date", "next_calibration_date", "weighbridge_id"]
        ),
        DocumentValidationRule(
            document_type="faturas_gas_natural",
            allowed_formats=[".pdf", ".xlsx"],
            max_size_mb=10,
            requires_digital_signature=False,
            mandatory_fields=["consumption_mwh", "invoice_period"]
        ),
        # Tomato / Agri-food
        DocumentValidationRule(
            document_type="certificado_sustentabilidade_biomassa",
            allowed_formats=[".pdf"],
            max_size_mb=5,
            requires_digital_signature=False,
            mandatory_fields=["biomass_type", "sustainability_criteria_met", "ghg_savings_pct"],
            must_contain_keywords=["RED II", "Directive 2018/2001", "sustainability"]
        ),
        DocumentValidationRule(
            document_type="calibracao_contador_vapor",
            allowed_formats=[".pdf"],
            max_size_mb=3,
            requires_digital_signature=False,
            mandatory_fields=["steam_meter_id", "calibration_date", "next_calibration_date"]
        )
    ]
    
    for r in rules:
        exists = db.query(DocumentValidationRule).filter_by(document_type=r.document_type).first()
        if not exists:
            db.add(r)
    db.commit()

def seed_initial_data(db: Session):
    """Orchestrates initial seed."""
    # Ensure Ceramic Organization Exists
    org_c = db.query(Organization).filter_by(vat_number="PT500123456").first()
    if not org_c:
        org_c = Organization(name="Ceramica Demo SA", vat_number="PT500123456", sector=SectorType.CERAMIC)
        db.add(org_c)
        db.commit()
    
    # Ensure Ceramic Installation Exists
    inst_c = db.query(Installation).filter_by(permit_id="TEGEH-2024-001").first()
    if not inst_c:
        inst_c = Installation(name="Factory 1", permit_id="TEGEH-2024-001", organization_id=org_c.id)
        db.add(inst_c)
        db.commit()
        
    seed_ceramic_data(db, inst_c.id)
    
    # Seed Tomato Data
    seed_tomato_data(db)
    
    # Global Configs
    seed_apa_task_definitions(db)
    seed_document_rules(db)
