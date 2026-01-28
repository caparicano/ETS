
import React, { useState } from 'react';
import { Bot, User, Upload, CheckCircle2, Factory, FileText, ArrowRight, Loader2 } from 'lucide-react';

interface WizardProps {
  onComplete: () => void;
  onCancel: () => void;
}

interface Message {
  role: 'ai' | 'user';
  text: string;
}

const SetupWizard: React.FC<WizardProps> = ({ onComplete, onCancel }) => {
  const [step, setStep] = useState<'upload' | 'chat' | 'preview'>('upload');
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [loading, setLoading] = useState(false);
  const [previewData, setPreviewData] = useState<any>(null);

  // MOCK API for Demo purposes
  // In real integration, replace with fetch calls to /api/v1/wizard/...
  const mockApi = {
    start: async (file: File) => {
      await new Promise(r => setTimeout(r, 1500));
      return {
        session_id: '123-abc',
        state: 'CONFIRM_EQUIPMENT',
        message: "I analyzed the permit for **Cerâmica Leiria**. I found:\n- Tunnel Kiln 1\n- Spray Dryer A\n\nIs this list correct?"
      };
    },
    chat: async (msg: string) => {
      await new Promise(r => setTimeout(r, 1000));
      if (msg.toLowerCase().includes('yes')) {
        return {
          session_id: '123-abc',
          state: 'FUEL_DETAILS',
          message: "Great. Regarding **Tunnel Kiln 1**: What is the primary fuel source?"
        };
      } else if (msg.toLowerCase().includes('gas')) {
        return {
            session_id: '123-abc',
            state: 'PREVIEW_CONFIG',
            message: "I have gathered all necessary information.",
            preview: {
                installation_name: "Cerâmica Leiria",
                streams: [
                    { name: "Tunnel Kiln 1 (Combustion)", fuel: "Natural Gas", tier: 2 },
                    { name: "Spray Dryer A (Combustion)", fuel: "Natural Gas", tier: 2 }
                ]
            }
        };
      }
      return { session_id: '123-abc', state: 'CHAT', message: "Could you clarify?" };
    },
    approve: async () => {
        await new Promise(r => setTimeout(r, 1000));
        return { status: 'success' };
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files?.[0]) return;
    setLoading(true);
    try {
      const res = await mockApi.start(e.target.files[0]);
      setSessionId(res.session_id);
      setMessages([{ role: 'ai', text: res.message }]);
      setStep('chat');
    } finally {
      setLoading(false);
    }
  };

  const handleSend = async () => {
    if (!inputValue.trim()) return;
    
    const userMsg = inputValue;
    setMessages(prev => [...prev, { role: 'user', text: userMsg }]);
    setInputValue('');
    setLoading(true);

    try {
      const res = await mockApi.chat(userMsg);
      setMessages(prev => [...prev, { role: 'ai', text: res.message }]);
      
      if (res.state === 'PREVIEW_CONFIG' && res.preview) {
        setPreviewData(res.preview);
        setStep('preview');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async () => {
    setLoading(true);
    await mockApi.approve();
    onComplete();
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-2xl overflow-hidden flex flex-col max-h-[80vh]">
        
        {/* Header */}
        <div className="bg-emerald-600 p-6 text-white flex justify-between items-center">
          <div>
            <h2 className="text-xl font-bold flex items-center gap-2">
              <Bot size={24} /> AI Setup Wizard
            </h2>
            <p className="text-emerald-100 text-sm mt-1">
               I will interview you to configure your installation based on your TEGEH permit.
            </p>
          </div>
          <button onClick={onCancel} className="text-emerald-200 hover:text-white">
             <Bot className="rotate-45" /> Exit
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6 bg-slate-50">
          
          {step === 'upload' && (
             <div className="text-center py-12">
                <div className="w-20 h-20 bg-emerald-100 rounded-full flex items-center justify-center mx-auto mb-6">
                    <FileText className="text-emerald-600 w-10 h-10" />
                </div>
                <h3 className="text-lg font-bold text-slate-800 mb-2">Upload TEGEH Permit</h3>
                <p className="text-slate-500 mb-8 max-w-sm mx-auto">
                    Upload your PDF permit. I will extract equipment lists and fuel authorizations automatically.
                </p>
                <label className="inline-block">
                    <input type="file" className="hidden" accept=".pdf" onChange={handleFileUpload} />
                    <div className="bg-emerald-600 text-white px-6 py-3 rounded-xl font-semibold cursor-pointer hover:bg-emerald-700 transition-colors flex items-center gap-2">
                        {loading ? <Loader2 className="animate-spin" /> : <Upload size={20} />}
                        Select PDF File
                    </div>
                </label>
             </div>
          )}

          {step === 'chat' && (
            <div className="space-y-4">
              {messages.map((m, idx) => (
                <div key={idx} className={`flex gap-3 ${m.role === 'user' ? 'flex-row-reverse' : ''}`}>
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${
                        m.role === 'ai' ? 'bg-emerald-100 text-emerald-600' : 'bg-slate-200 text-slate-600'
                    }`}>
                        {m.role === 'ai' ? <Bot size={18} /> : <User size={18} />}
                    </div>
                    <div className={`px-4 py-3 rounded-2xl max-w-[80%] text-sm whitespace-pre-line ${
                        m.role === 'ai' ? 'bg-white border border-slate-200 text-slate-700' : 'bg-emerald-600 text-white'
                    }`}>
                        {m.text}
                    </div>
                </div>
              ))}
              {loading && (
                 <div className="flex gap-3">
                    <div className="w-8 h-8 rounded-full bg-emerald-100 flex items-center justify-center">
                        <Loader2 className="animate-spin text-emerald-600 w-4 h-4" />
                    </div>
                    <div className="text-xs text-slate-400 py-2">Analyzing...</div>
                 </div>
              )}
            </div>
          )}

          {step === 'preview' && previewData && (
             <div className="space-y-6">
                <div className="bg-emerald-50 border border-emerald-100 rounded-xl p-4 text-emerald-800 flex items-start gap-3">
                    <CheckCircle2 className="shrink-0 mt-0.5" />
                    <div>
                        <h4 className="font-bold">Configuration Ready</h4>
                        <p className="text-sm mt-1">I've generated the monitoring plan based on our conversation. Please review before creating the digital twin.</p>
                    </div>
                </div>

                <div className="bg-white border border-slate-200 rounded-xl overflow-hidden">
                    <div className="p-4 bg-slate-50 border-b border-slate-200 font-semibold text-slate-700">
                        {previewData.installation_name}
                    </div>
                    <div className="p-4 space-y-3">
                        {previewData.streams.map((s: any, i: number) => (
                            <div key={i} className="flex justify-between items-center p-3 border border-slate-100 rounded-lg">
                                <div className="flex items-center gap-3">
                                    <Factory className="text-slate-400" size={18} />
                                    <div>
                                        <div className="font-medium text-slate-800">{s.name}</div>
                                        <div className="text-xs text-slate-500">Method: Standard • Tier {s.tier}</div>
                                    </div>
                                </div>
                                <div className="px-2 py-1 bg-emerald-100 text-emerald-700 text-xs font-bold rounded uppercase">
                                    {s.fuel}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
             </div>
          )}

        </div>

        {/* Footer */}
        {step === 'chat' && (
          <div className="p-4 bg-white border-t border-slate-200 flex gap-2">
            <input 
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                placeholder="Type your answer..."
                className="flex-1 px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-emerald-500 outline-none"
            />
            <button onClick={handleSend} disabled={loading} className="bg-emerald-600 text-white p-2 rounded-lg hover:bg-emerald-700">
                <ArrowRight size={20} />
            </button>
          </div>
        )}
        
        {step === 'preview' && (
            <div className="p-4 bg-white border-t border-slate-200 flex justify-end gap-3">
                <button onClick={() => setStep('chat')} className="px-4 py-2 text-slate-500 font-medium hover:bg-slate-50 rounded-lg">
                    Back to Edit
                </button>
                <button onClick={handleApprove} className="px-6 py-2 bg-emerald-600 text-white font-bold rounded-lg hover:bg-emerald-700 flex items-center gap-2">
                    {loading ? <Loader2 className="animate-spin" /> : <CheckCircle2 size={18} />}
                    Approve & Create
                </button>
            </div>
        )}

      </div>
    </div>
  );
};

export default SetupWizard;
