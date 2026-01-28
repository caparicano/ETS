
import React, { useState, useEffect } from 'react';
import { 
  CheckCircle2, AlertTriangle, Upload, FileText, Clock, 
  ChevronRight, Calendar, Scale, Microscope, Flame, Globe, Droplets, Factory, X, Loader2
} from 'lucide-react';
import { ComplianceTask, EvidenceDoc } from '../types'; // Note: Type definitions might need update to match API
import DynamicEmissionForm from './DynamicEmissionForm';

type IndustryType = 'ceramic' | 'tomato';

interface APITask {
    id: number;
    title: string;
    task_code: string;
    description: string;
    due_date: string;
    status: string;
    priority: number;
    category: string;
}

const ComplianceManager: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'tasks' | 'evidence'>('tasks');
  const [industry, setIndustry] = useState<IndustryType>('ceramic');
  const [selectedTask, setSelectedTask] = useState<APITask | null>(null);
  
  const [tasks, setTasks] = useState<APITask[]>([]);
  const [loading, setLoading] = useState(false);
  const [nextDeadline, setNextDeadline] = useState<{date: string, days: number} | null>(null);

  // --- FETCH DATA ---
  useEffect(() => {
    const fetchTasks = async () => {
        setLoading(true);
        try {
            // Mock API call simulation for Phase 1.2 Demo
            // In real integration: await fetch(`/api/v1/tasks?installation_id=1`);
            await new Promise(r => setTimeout(r, 600)); 
            
            // Hardcoded response that matches the new DB schema structure
            const mockData: APITask[] = [
                { id: 101, task_code: 'monthly_input_gas', title: 'Registo Mensal: Gás Natural (Janeiro)', description: 'Inserir leituras...', due_date: '2025-02-15', status: 'PENDING', priority: 5, category: 'Data' },
                { id: 102, task_code: 'verification', title: 'Obter Parecer de Verificação', description: 'Garantir validação...', due_date: '2025-03-15', status: 'PENDING', priority: 1, category: 'Admin' },
                { id: 103, task_code: 'submit_re', title: 'Submeter Relatório de Emissões (RE)', description: 'Submissão via SILiAmb.', due_date: '2025-03-31', status: 'PENDING', priority: 1, category: 'Compliance' },
                { id: 104, task_code: 'rple_surrender', title: 'Entrega de Licenças (RPLE)', description: 'Entrega de licenças...', due_date: '2025-04-30', status: 'PENDING', priority: 1, category: 'Surrender' },
            ];
            
            setTasks(mockData);
            
            // Calc next deadline
            const next = mockData[0]; // Assuming sorted
            if(next) {
                const days = Math.ceil((new Date(next.due_date).getTime() - new Date().getTime()) / (1000 * 3600 * 24));
                setNextDeadline({ date: next.due_date, days });
            }

        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    };
    fetchTasks();
  }, [industry]);

  // Fallback static evidence for demo
  const ceramicEvidence = [
    {
      id: 'official',
      title: 'Official Reports (SILiAmb)',
      icon: <Globe className="w-5 h-5 text-blue-600" />,
      docs: [
        { id: 'd1', name: 'Relatorio_Emissoes_2023.pdf', type: 'RE', status: 'verified', dateUploaded: '2024-03-15' },
      ] as EvidenceDoc[]
    }
  ];

  return (
    <div className="flex h-full flex-col relative">
      {/* Industry Switcher Header */}
      <div className="bg-white border-b border-slate-200 px-8 py-4 flex justify-between items-center sticky top-0 z-10 shadow-sm">
         <div className="flex items-center gap-3">
            <div className={`p-2 rounded-lg ${industry === 'ceramic' ? 'bg-orange-100 text-orange-600' : 'bg-red-100 text-red-600'}`}>
              <Factory size={20} />
            </div>
            <div>
              <h2 className="text-sm font-semibold text-slate-500 uppercase tracking-wide">Active Sector</h2>
              <select 
                value={industry}
                onChange={(e) => setIndustry(e.target.value as IndustryType)}
                className="text-lg font-bold text-slate-800 bg-transparent border-none focus:ring-0 p-0 cursor-pointer"
              >
                <option value="ceramic">Cerâmica (ex: Tijolos & Telhas)</option>
                <option value="tomato">Agro-Alimentar (ex: Sugal / Tomate)</option>
              </select>
            </div>
         </div>
         <div className="flex gap-4 text-sm text-slate-500">
            {industry === 'tomato' && (
              <div className="flex items-center gap-2 px-3 py-1 bg-red-50 text-red-700 rounded-full border border-red-100">
                 <Clock size={14} /> Campaign Status: <strong>OFF-SEASON</strong>
              </div>
            )}
         </div>
      </div>

      <div className="flex flex-1 overflow-hidden">
        {/* Main Content Area */}
        <div className="flex-1 p-8 overflow-y-auto">
          
          {/* Header with Progress */}
          <div className="mb-8">
            <div className="flex justify-between items-end mb-6">
              <div>
                <h1 className="text-3xl font-bold text-slate-800">Compliance Manager (Portugal)</h1>
                <p className="text-slate-500 mt-1">
                  Task Engine Active • Generated from MRR 2018/2066 Rules
                </p>
              </div>
              {nextDeadline && (
                <div className="text-right">
                    <div className="text-sm font-medium text-slate-500 mb-1">Next Major Deadline</div>
                    <div className={`text-xl font-bold flex items-center justify-end gap-2 ${
                        nextDeadline.days < 30 ? 'text-amber-600' : 'text-emerald-600'
                    }`}>
                    <Calendar className="w-5 h-5" /> {new Date(nextDeadline.date).toLocaleDateString()}
                    </div>
                    <div className="text-xs text-slate-400">
                        {nextDeadline.days} days remaining
                    </div>
                </div>
              )}
            </div>

            {/* Workflow Stepper */}
            <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200">
              <div className="flex items-center justify-between relative">
                <div className="absolute left-0 top-1/2 w-full h-1 bg-slate-100 -z-0"></div>
                {[
                  { label: 'Data Collection', active: true, done: false },
                  { label: 'SILiAmb Submission', active: false, done: false },
                  { label: 'Verification', active: false, done: false },
                  { label: 'RPLE Surrender', active: false, done: false }
                ].map((step, idx) => (
                  <div key={idx} className="relative z-10 flex flex-col items-center gap-2 bg-white px-4">
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold transition-all ${
                      step.active ? 'bg-emerald-600 text-white ring-4 ring-emerald-100' : 'bg-slate-200 text-slate-500'
                    }`}>
                      {idx + 1}
                    </div>
                    <span className={`text-sm font-medium ${step.active ? 'text-emerald-700' : 'text-slate-400'}`}>
                      {step.label}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Navigation Tabs */}
          <div className="flex gap-6 border-b border-slate-200 mb-6">
            <button 
              onClick={() => setActiveTab('tasks')}
              className={`pb-3 px-1 font-medium text-sm transition-colors relative ${
                activeTab === 'tasks' ? 'text-emerald-600' : 'text-slate-500 hover:text-slate-700'
              }`}
            >
              Pending Tasks
              {activeTab === 'tasks' && <div className="absolute bottom-0 left-0 w-full h-0.5 bg-emerald-600 rounded-t-full"></div>}
            </button>
            <button 
              onClick={() => setActiveTab('evidence')}
              className={`pb-3 px-1 font-medium text-sm transition-colors relative ${
                activeTab === 'evidence' ? 'text-emerald-600' : 'text-slate-500 hover:text-slate-700'
              }`}
            >
              Evidence Vault
              {activeTab === 'evidence' && <div className="absolute bottom-0 left-0 w-full h-0.5 bg-emerald-600 rounded-t-full"></div>}
            </button>
          </div>

          {/* Tasks View */}
          {activeTab === 'tasks' && (
            <div className="space-y-4">
              {loading && <div className="p-8 text-center text-slate-400"><Loader2 className="animate-spin mx-auto mb-2" /> Loading Tasks...</div>}
              
              {!loading && tasks.map(task => (
                <div 
                    key={task.id} 
                    onClick={() => task.task_code.includes('monthly') ? setSelectedTask(task) : null}
                    className={`bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex items-center justify-between hover:shadow-md transition-shadow group cursor-pointer ${
                        task.task_code.includes('monthly') ? 'ring-2 ring-emerald-500 ring-offset-2' : ''
                    }`}
                >
                  <div className="flex items-center gap-4">
                    <div className={`w-10 h-10 rounded-full flex items-center justify-center shrink-0 ${
                      task.status === 'COMPLETED' ? 'bg-emerald-100 text-emerald-600' : 
                      task.status === 'OVERDUE' ? 'bg-red-100 text-red-600' : 'bg-slate-100 text-slate-500'
                    }`}>
                      {task.status === 'COMPLETED' ? <CheckCircle2 size={20} /> : <Clock size={20} />}
                    </div>
                    <div>
                      <h3 className="font-semibold text-slate-800">{task.title}</h3>
                      <p className="text-sm text-slate-500">Due: {task.due_date} • {task.category}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className={`px-3 py-1 rounded-full text-xs font-medium capitalize ${
                      task.status === 'COMPLETED' ? 'bg-emerald-50 text-emerald-700 border border-emerald-100' :
                      task.status === 'OVERDUE' ? 'bg-red-50 text-red-700 border border-red-100' :
                      'bg-amber-50 text-amber-700 border border-amber-100'
                    }`}>
                      {task.status.toLowerCase()}
                    </span>
                    <ChevronRight className="text-slate-300 group-hover:text-emerald-500 transition-colors" size={20} />
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Evidence View (Simplified for now) */}
          {activeTab === 'evidence' && (
            <div className="space-y-6">
                <div className="bg-white p-8 text-center border border-slate-200 rounded-xl text-slate-400">
                    Evidence Vault connected to S3 (Mock)
                </div>
            </div>
          )}
        </div>

        {/* AI Auditor Sidebar */}
        <div className="w-80 bg-white border-l border-slate-200 p-6 flex flex-col z-20 shadow-[-4px_0_15px_-3px_rgba(0,0,0,0.05)]">
          <div className="flex items-center gap-2 mb-6">
            <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></div>
            <h3 className="font-semibold text-slate-800">AI Auditor</h3>
          </div>
          <div className="text-sm text-slate-600">
             Monitoring <strong>{tasks.length}</strong> compliance tasks.
          </div>
        </div>
      </div>

      {/* DYNAMIC FORM MODAL OVERLAY */}
      {selectedTask && (
        <div className="absolute inset-0 z-50 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4">
            <div className="w-full max-w-2xl relative">
                <button 
                    onClick={() => setSelectedTask(null)}
                    className="absolute -top-12 right-0 text-white/80 hover:text-white flex items-center gap-2"
                >
                    Close <X size={20} />
                </button>
                <div className="bg-white rounded-t-2xl p-4 border-b">
                    <h3 className="font-bold">{selectedTask.title}</h3>
                    <p className="text-sm text-slate-500">Task ID: {selectedTask.id}</p>
                </div>
                <DynamicEmissionForm 
                    sourceStreamId={1} 
                    onSuccess={() => {
                        // Refresh tasks
                        setSelectedTask(null);
                    }}
                />
            </div>
        </div>
      )}

    </div>
  );
};

export default ComplianceManager;
