
import io
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from backend.infrastructure.models import Installation, EmissionEntry

class APAReportGenerator:
    def __init__(self, db: Session):
        self.db = db

    def generate_relatorio_emissoes(self, installation_id: int, year: int) -> bytes:
        """
        Generate official RE (Relatório de Emissões) PDF.
        """
        inst = self.db.query(Installation).get(installation_id)
        if not inst: raise ValueError("Installation not found")
        
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        
        # --- Header ---
        p.setFont("Helvetica-Bold", 16)
        p.drawString(50, height - 50, "RELATÓRIO DE EMISSÕES (RE) - EU ETS")
        p.setFont("Helvetica", 10)
        p.drawString(50, height - 70, f"Ano de Relato: {year}")
        p.drawString(50, height - 85, f"Instalação: {inst.name} ({inst.permit_id})")
        p.drawString(50, height - 100, f"Operador: {inst.organization.name} (NIF: {inst.organization.vat_number})")
        
        p.line(50, height - 110, width - 50, height - 110)
        
        # --- Executive Summary ---
        # Calculate Total Emissions
        total_emissions = self.db.query(func.sum(EmissionEntry.calculated_tco2)).filter(
            EmissionEntry.installation_id == installation_id,
            extract('year', EmissionEntry.date_start) == year
        ).scalar() or 0.0
        
        p.setFont("Helvetica-Bold", 12)
        p.drawString(50, height - 140, "1. Sumário Executivo")
        p.setFont("Helvetica", 10)
        p.drawString(50, height - 160, f"Total de Emissões Verificadas: {total_emissions:,.2f} tCO2e")
        
        # --- Source Streams ---
        p.setFont("Helvetica-Bold", 12)
        p.drawString(50, height - 200, "2. Detalhe por Fonte de Emissão")
        
        y_pos = height - 230
        p.setFont("Helvetica-Bold", 9)
        p.drawString(50, y_pos, "Fonte")
        p.drawString(250, y_pos, "Combustível")
        p.drawString(400, y_pos, "Emissões (tCO2)")
        
        y_pos -= 20
        p.setFont("Helvetica", 9)
        
        for stream in inst.source_streams:
            stream_total = self.db.query(func.sum(EmissionEntry.calculated_tco2)).filter(
                EmissionEntry.source_stream_id == stream.id,
                extract('year', EmissionEntry.date_start) == year
            ).scalar() or 0.0
            
            p.drawString(50, y_pos, stream.name[:35])
            p.drawString(250, y_pos, stream.fuel_or_material)
            p.drawString(400, y_pos, f"{stream_total:,.2f}")
            y_pos -= 15
            
        # --- Methodology Citation ---
        y_pos -= 40
        p.setFont("Helvetica-Bold", 12)
        p.drawString(50, y_pos, "3. Metodologia e Conformidade")
        y_pos -= 20
        p.setFont("Helvetica", 9)
        p.drawString(50, y_pos, "Cálculo realizado de acordo com o Regulamento (UE) 2018/2066 (MRR).")
        y_pos -= 15
        p.drawString(50, y_pos, "Fatores de emissão baseados no Anexo VI ou análises laboratoriais acreditadas.")
        
        # --- Signature Block ---
        y_pos -= 80
        p.line(50, y_pos, 250, y_pos)
        p.drawString(50, y_pos - 15, "Assinatura do Responsável")
        p.drawString(50, y_pos - 30, f"Data: {datetime.now().strftime('%Y-%m-%d')}")
        
        p.showPage()
        p.save()
        buffer.seek(0)
        return buffer.getvalue()

    def generate_relatorio_nivel_atividade(self, installation_id: int, year: int) -> bytes:
        """Stub for ALC Report."""
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=A4)
        p.drawString(100, 750, f"Relatório de Nível de Atividade (ALC) - {year}")
        p.drawString(100, 730, "TODO: Implement HAL vs ALC comparison logic.")
        p.showPage()
        p.save()
        buffer.seek(0)
        return buffer.getvalue()

    def generate_verification_package(self, installation_id: int, year: int) -> Dict[str, bytes]:
        """
        In a real app, this returns a ZIP. 
        For now returns a Dict of filenames to bytes.
        """
        return {
            f"RE_{year}.pdf": self.generate_relatorio_emissoes(installation_id, year),
            f"ALC_{year}.pdf": self.generate_relatorio_nivel_atividade(installation_id, year)
        }
