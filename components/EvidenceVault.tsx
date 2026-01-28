
import React, { useState, useEffect } from 'react';
import { 
  FileText, Upload, ShieldCheck, AlertTriangle, Eye, Lock, 
  Trash2, Search, Loader2, CheckCircle2, XCircle
} from 'lucide-react';
import { EvidenceDoc, APADocumentType } from '../types';

interface EvidenceVaultProps {
  installationId: number;
  year: number;
}

// Map technical types to friendly names
const DOC_TYPE_LABELS: Record<string, string> = {
  [APADocumentType.RELATORIO_EMISSOES]: "Relatório de Emissões (RE)",
  [APADocumentType.PARECER_VERIFICACAO]: "Parecer de Verificação",
  [APADocumentType.FATURAS_GAS_NATURAL]: "Faturas de Gás Natural",
  [APADocumentType.ANALISE_CARBONATOS_ARGILA]: "Análise Laboratorial (Carbonatos)",
  [APADocumentType.CERTIFICADO_CALIBRACAO_BALANCA]: "Certificado Calibração Balança",
  [APADocumentType.CERTIFICADO_SUSTENTABILIDADE_BIOMASSA]: "Certificado Sustentabilidade (RED II)"
};

const EvidenceVault: React.FC<EvidenceVaultProps> = ({ installationId, year }) => {
  const [documents, setDocuments] = useState<EvidenceDoc[]>([]);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [selectedType, setSelectedType] = useState<string>(APADocumentType.FATURAS_GAS_NATURAL);
  const [dragActive, setDragActive] = useState(false);

  // Fetch Documents
  const fetchDocuments = async () => {
    setLoading(true);
    try {
      // In real app: await fetch(`/api/v1/documents?installation_id=${installationId}&year=${year}`)
      // Simulating API response
      await new Promise(r => setTimeout(r, 600));
      const mockDocs: EvidenceDoc[] = [
        {
           id: 1, 
           filename: "Fatura_Jan_2024.pdf", 
           document_type: APADocumentType.FATURAS_GAS_NATURAL, 
           status: 'VERIFIED', 
           upload_date: '2024-02-15T10:00:00', 
           version: 1 
        },
        {
           id: 2, 
           filename: "Analise_Lab_Q1.pdf", 
           document_type: APADocumentType.ANALISE_CARBONATOS_ARGILA, 
           status: 'OCR_FAILED', 
           upload_date: '2024-03-01T14:30:00', 
           version: 1,
           extracted_text_snippet: "Sample analysis... missing ISO 17025 reference..."
        }
      ];
      setDocuments(mockDocs);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, [installationId, year]);

  // Handle Upload
  const handleFileUpload = async (files: FileList | null) => {
    if (!files || files.length === 0) return;
    
    setUploading(true);
    const file = files[0];
    
    try {
      // In real app:
      // const formData = new FormData();
      // formData.append('file', file);
      // formData.append('document_type', selectedType);
      // formData.append('installation_id', installationId.toString());
      // formData.append('reporting_year', year.toString());
      // await fetch('/api/v1/documents/upload', { method: 'POST', body: formData });
      
      await new Promise(r => setTimeout(r, 1500)); // Simulate OCR processing
      
      const newDoc: EvidenceDoc = {
        id: Math.random(),
        filename: file.name,
        document_type: selectedType,
        status: file.name.includes("error") ? 'OCR_FAILED' : 'PENDING', // Simulating result
        upload_date: new Date().toISOString(),
        version: 1,
        message: file.name.includes("error") ? "Missing mandatory keywords: ISO 17025" : "Uploaded successfully"
      };
      
      setDocuments(prev => [newDoc, ...prev]);
    } catch (e) {
      console.error("Upload failed", e);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="space-y-6">
      
      {/* Upload Area */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
        <h3 className="text-lg font-bold text-slate-800 mb-4 flex items-center gap-2">
          <Upload className="text-emerald-600" size={20} /> Upload Evidence
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          <div className="md:col-span-1">
            <label className="block text-sm font-semibold text-slate-700 mb-2">Document Type</label>
            <select 
              value={selectedType}
              onChange={(e) => setSelectedType(e.target.value)}
              className="w-full p-2.5 rounded-xl border border-slate-200 bg-slate-50 text-sm focus:ring-2 focus:ring-emerald-500 outline-none"
            >
              {Object.entries(DOC_TYPE_LABELS).map(([value, label]) => (
                <option key={value} value={value}>{label}</option>
              ))}
            </select>
          </div>
          
          <div className="md:col-span-2">
             <label className="block text-sm font-semibold text-slate-700 mb-2">File (PDF, XLSX)</label>
             <div 
               className={`border-2 border-dashed rounded-xl p-6 text-center transition-colors ${
                 uploading ? 'bg-slate-50 border-slate-300' : 'border-emerald-200 hover:bg-emerald-50 cursor-pointer'
               }`}
             >
                <input 
                  type="file" 
                  id="file-upload" 
                  className="hidden" 
                  onChange={(e) => handleFileUpload(e.target.files)}
                  disabled={uploading}
                  accept=".pdf,.xlsx,.csv"
                />
                <label htmlFor="file-upload" className="cursor-pointer w-full h-full block">
                  {uploading ? (
                    <div className="flex flex-col items-center gap-2 text-slate-500">
                      <Loader2 className="animate-spin text-emerald-600" />
                      <span className="text-xs">Scanning document with AI OCR...</span>
                    </div>
                  ) : (
                    <div className="text-slate-500">
                      <span className="text-emerald-600 font-semibold">Click to upload</span> or drag and drop
                      <p className="text-xs mt-1 text-slate-400">Max 10MB • Secured Storage</p>
                    </div>
                  )}
                </label>
             </div>
          </div>
        </div>
      </div>

      {/* Document List */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="p-4 border-b border-slate-100 flex justify-between items-center bg-slate-50">
          <h3 className="font-bold text-slate-700 flex items-center gap-2">
            <ShieldCheck size={18} /> Evidence Vault ({year})
          </h3>
          <span className="text-xs font-mono text-slate-400">
            {documents.length} Documents • Mock S3
          </span>
        </div>

        {loading ? (
          <div className="p-8 text-center text-slate-400">Loading documents...</div>
        ) : documents.length === 0 ? (
           <div className="p-12 text-center text-slate-400 opacity-60">
             <FileText size={48} className="mx-auto mb-3" />
             <p>No documents uploaded for {year}</p>
           </div>
        ) : (
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-slate-500 font-semibold border-b border-slate-200">
              <tr>
                <th className="p-4">Document Name</th>
                <th className="p-4">Type</th>
                <th className="p-4">Status</th>
                <th className="p-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {documents.map((doc) => (
                <tr key={doc.id} className="hover:bg-slate-50 transition-colors">
                  <td className="p-4">
                    <div className="flex items-center gap-3">
                      <div className="p-2 bg-blue-50 text-blue-600 rounded-lg">
                        <FileText size={18} />
                      </div>
                      <div>
                        <div className="font-medium text-slate-800">{doc.filename}</div>
                        <div className="text-xs text-slate-400">v{doc.version} • {new Date(doc.upload_date).toLocaleDateString()}</div>
                      </div>
                    </div>
                  </td>
                  <td className="p-4 text-slate-600">
                    {DOC_TYPE_LABELS[doc.document_type] || doc.document_type}
                  </td>
                  <td className="p-4">
                    {doc.status === 'VERIFIED' && (
                      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold bg-emerald-100 text-emerald-700">
                        <CheckCircle2 size={12} /> Verified
                      </span>
                    )}
                    {doc.status === 'PENDING' && (
                      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold bg-amber-100 text-amber-700">
                        <Loader2 size={12} className="animate-spin" /> Processing
                      </span>
                    )}
                    {doc.status === 'OCR_FAILED' && (
                      <div className="flex flex-col items-start gap-1">
                        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold bg-red-100 text-red-700">
                            <AlertTriangle size={12} /> OCR Check Failed
                        </span>
                        {doc.extracted_text_snippet && (
                            <span className="text-[10px] text-red-500 max-w-[200px] truncate" title={doc.extracted_text_snippet}>
                                Issue: Keyword mismatch
                            </span>
                        )}
                      </div>
                    )}
                  </td>
                  <td className="p-4 text-right">
                    <div className="flex items-center justify-end gap-2">
                       <button className="p-1.5 text-slate-400 hover:text-blue-600 hover:bg-blue-50 rounded transition-colors" title="Preview">
                         <Eye size={16} />
                       </button>
                       {doc.status === 'LOCKED' ? (
                         <span className="p-1.5 text-slate-300">
                            <Lock size={16} />
                         </span>
                       ) : (
                         <button className="p-1.5 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded transition-colors" title="Delete">
                            <Trash2 size={16} />
                         </button>
                       )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};

export default EvidenceVault;
