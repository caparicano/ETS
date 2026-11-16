import React, { useState } from 'react';
import { BookOpen, Search, CheckCircle2, RefreshCw, FileText, Database } from 'lucide-react';
import { RegulatoryDoc } from '../types';
import { useGuideSection } from './guide/GuideContext';

const RegulatoryLibrary: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('');

  const documents: RegulatoryDoc[] = [
    { id: '1', title: 'Directive 2003/87/EC (Consolidated)', type: 'EU Directive', lastUpdated: '2023-06-05', status: 'indexed', chunkCount: 1450 },
    { id: '2', title: 'Regulation (EU) 2018/2066 (MRR)', type: 'Regulation', lastUpdated: '2024-01-01', status: 'indexed', chunkCount: 2100 },
    { id: '3', title: 'Regulation (EU) 2018/2067 (AVR)', type: 'Regulation', lastUpdated: '2019-01-01', status: 'indexed', chunkCount: 1200 },
    { id: '4', title: 'Portaria n.º 256/2015 (SILiAmb)', type: 'Portuguese Law', lastUpdated: '2015-08-01', status: 'indexed', chunkCount: 450 },
    { id: '5', title: 'Guidance Document 3: Biomass issues', type: 'Guidance', lastUpdated: '2022-10-17', status: 'processing', chunkCount: 0 },
  ];

  const filteredDocs = documents.filter(doc => 
    doc.title.toLowerCase().includes(searchTerm.toLowerCase()) || 
    doc.type.toLowerCase().includes(searchTerm.toLowerCase())
  );

  useGuideSection('biblioteca', {
    pesquisa: searchTerm,
    documentosVisiveis: filteredDocs.map((d) => ({ titulo: d.title, tipo: d.type, estado: d.status, atualizado: d.lastUpdated })),
  });

  return (
    <div className="p-8 max-w-7xl mx-auto h-full flex flex-col">
      <div className="flex justify-between items-end mb-8">
        <div>
          <h1 className="text-3xl font-bold text-slate-800">Regulatory Knowledge Base</h1>
          <p className="text-slate-500 mt-1">The "Brain" of CeramETS. Managing ingested laws for RAG retrieval.</p>
        </div>
        <div className="flex gap-3">
            <button className="flex items-center gap-2 px-4 py-2 bg-white border border-slate-200 rounded-lg text-slate-600 hover:bg-slate-50 font-medium">
                <RefreshCw size={18} /> Re-Index
            </button>
            <button className="flex items-center gap-2 px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 font-medium shadow-sm">
                + Ingest New Document
            </button>
        </div>
      </div>

      <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200 mb-8">
        <div className="flex gap-4 mb-6">
            <div className="flex-1 relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={20} />
                <input 
                    type="text" 
                    placeholder="Search regulation library..." 
                    className="w-full pl-10 pr-4 py-3 rounded-xl border border-slate-200 focus:ring-2 focus:ring-emerald-500 outline-none"
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                />
            </div>
            <div className="flex items-center gap-2 px-4 py-2 bg-slate-50 rounded-xl border border-slate-200">
                <Database className="text-emerald-600" size={20} />
                <div className="flex flex-col">
                    <span className="text-xs text-slate-400 uppercase font-bold">Total Chunks</span>
                    <span className="text-sm font-bold text-slate-800">5,200 Vectors</span>
                </div>
            </div>
        </div>

        <div className="overflow-hidden rounded-xl border border-slate-200">
            <table className="w-full text-left border-collapse">
                <thead className="bg-slate-50 text-slate-500 text-xs uppercase font-semibold">
                    <tr>
                        <th className="p-4 border-b border-slate-200">Document Title</th>
                        <th className="p-4 border-b border-slate-200">Type</th>
                        <th className="p-4 border-b border-slate-200">Last Updated</th>
                        <th className="p-4 border-b border-slate-200">Status</th>
                        <th className="p-4 border-b border-slate-200 text-right">Vectors</th>
                    </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                    {filteredDocs.map(doc => (
                        <tr key={doc.id} className="hover:bg-slate-50 transition-colors">
                            <td className="p-4 font-medium text-slate-800 flex items-center gap-3">
                                <div className="p-2 bg-emerald-50 rounded text-emerald-600">
                                    <FileText size={18} />
                                </div>
                                {doc.title}
                            </td>
                            <td className="p-4">
                                <span className={`px-2 py-1 rounded text-xs font-semibold ${
                                    doc.type === 'EU Directive' ? 'bg-blue-100 text-blue-700' :
                                    doc.type === 'Regulation' ? 'bg-purple-100 text-purple-700' :
                                    'bg-slate-100 text-slate-600'
                                }`}>
                                    {doc.type}
                                </span>
                            </td>
                            <td className="p-4 text-slate-500 text-sm">{doc.lastUpdated}</td>
                            <td className="p-4">
                                <span className={`flex items-center gap-1.5 text-xs font-medium ${
                                    doc.status === 'indexed' ? 'text-emerald-600' : 
                                    doc.status === 'processing' ? 'text-amber-600' : 'text-red-600'
                                }`}>
                                    {doc.status === 'indexed' ? <CheckCircle2 size={14} /> : <RefreshCw size={14} className="animate-spin" />}
                                    {doc.status.charAt(0).toUpperCase() + doc.status.slice(1)}
                                </span>
                            </td>
                            <td className="p-4 text-right text-slate-500 font-mono text-sm">{doc.chunkCount.toLocaleString()}</td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
      </div>
    </div>
  );
};

export default RegulatoryLibrary;