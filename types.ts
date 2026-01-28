
export enum AppView {
  LANDING = 'LANDING',
  CONSULTATION = 'CONSULTATION',
  DASHBOARD = 'DASHBOARD',
  COMPLIANCE = 'COMPLIANCE',
  LIBRARY = 'LIBRARY'
}

export interface Message {
  role: 'user' | 'model';
  text: string;
  isThinking?: boolean;
  citations?: SourceCitation[];
}

export interface SourceCitation {
  docId: string;
  docTitle: string;
  article: string;
  snippet: string;
  relevance: number;
}

export interface RegulatoryDoc {
  id: string;
  title: string;
  type: 'EU Directive' | 'Regulation' | 'Portuguese Law' | 'Guidance';
  lastUpdated: string;
  status: 'indexed' | 'processing' | 'error';
  chunkCount: number;
}

export interface ETSMetric {
  year: number;
  verifiedEmissions: number;
  freeAllocation: number;
  carbonPrice: number;
}

export interface StrategicAdvice {
  title: string;
  description: string;
  impact: 'High' | 'Medium' | 'Low';
  cost: '$$$' | '$$' | '$';
  timeframe: string;
}

export interface ConsultantContext {
  companyName: string;
  kilnType: string;
  fuelType: string;
  annualProduction: string;
}

export interface ComplianceTask {
  id: string;
  title: string;
  dueDate: string;
  status: 'pending' | 'completed' | 'overdue';
  category: 'Data' | 'Admin' | 'Surrender';
}

export enum APADocumentType {
  RELATORIO_EMISSOES = "relatorio_emissoes",
  PARECER_VERIFICACAO = "parecer_verificacao",
  FATURAS_GAS_NATURAL = "faturas_gas_natural",
  ANALISE_CARBONATOS_ARGILA = "analise_carbonatos_argila",
  CERTIFICADO_CALIBRACAO_BALANCA = "certificado_calibracao_balanca",
  CERTIFICADO_SUSTENTABILIDADE_BIOMASSA = "certificado_sustentabilidade_biomassa"
}

export interface EvidenceDoc {
  id: number;
  filename: string;
  document_type: string;
  status: 'PENDING' | 'VERIFIED' | 'REJECTED' | 'LOCKED' | 'OCR_FAILED';
  upload_date: string;
  version: number;
  extracted_text_snippet?: string;
  message?: string;
}
