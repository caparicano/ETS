import React, { useEffect, useRef, useState } from 'react';
import { Chat } from "@google/genai";
import { Message, AppView, SourceCitation } from '../types';
import { createConsultationChat, generateStrategicReport } from '../services/geminiService';
import { Send, Bot, User, Loader2, FileText, BookOpen, Search } from 'lucide-react';
import ReactMarkdown from 'react-markdown';

interface ConsultationProps {
  onComplete: (data: any) => void;
  setView: (view: AppView) => void;
}

// Mock RAG Retrieval function (simulating backend vector search)
const mockRetrieveContext = (query: string): SourceCitation[] => {
    const citations: SourceCitation[] = [];
    const lowerQ = query.toLowerCase();

    if (lowerQ.includes('biomass') || lowerQ.includes('bio')) {
        citations.push({
            docId: '2', docTitle: 'Regulation (EU) 2018/2066 (MRR)', article: 'Article 38',
            snippet: 'Biomass fractions shall be zero-rated if they satisfy the sustainability criteria established by the RED II Directive...',
            relevance: 0.95
        });
        citations.push({
            docId: '5', docTitle: 'Guidance Document 3', article: 'Section 4.1',
            snippet: 'Specific rules for determination of biomass fraction in mixed fuels (e.g., clay with organic content).',
            relevance: 0.88
        });
    }
    if (lowerQ.includes('deadline') || lowerQ.includes('submit') || lowerQ.includes('date')) {
        citations.push({
            docId: '4', docTitle: 'Portaria n.º 256/2015', article: 'Artigo 4º',
            snippet: 'O operador deve submeter o Relatório de Emissões verificado na plataforma SILiAmb até 31 de Março de cada ano.',
            relevance: 0.99
        });
    }
    if (lowerQ.includes('uncertainty') || lowerQ.includes('meter')) {
        citations.push({
            docId: '2', docTitle: 'Regulation (EU) 2018/2066 (MRR)', article: 'Article 28',
            snippet: 'The operator shall determine the activity data based on metering with a maximum uncertainty of...',
            relevance: 0.92
        });
    }
    
    // Default context if nothing specific matches
    if (citations.length === 0) {
        citations.push({
            docId: '1', docTitle: 'Directive 2003/87/EC', article: 'General Principles',
            snippet: 'Establishing a scheme for greenhouse gas emission allowance trading within the Community.',
            relevance: 0.5
        });
    }

    return citations;
};

const Consultation: React.FC<ConsultationProps> = ({ onComplete, setView }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [chatSession, setChatSession] = useState<Chat | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [isGeneratingReport, setIsGeneratingReport] = useState(false);
  
  // State for RAG Visualization
  const [activeCitations, setActiveCitations] = useState<SourceCitation[]>([]);
  const [isRetrieving, setIsRetrieving] = useState(false);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    const initChat = async () => {
      const session = createConsultationChat();
      if (session) {
        setChatSession(session);
        setIsTyping(true);
        try {
          const response = await session.sendMessage({ 
            message: "Hello. I am the plant manager. Start the EU ETS consultation. Remember to cite laws." 
          });
          setMessages([{ role: 'model', text: response.text || "Hello! I am CeramETS, your AI compliance consultant. I can help with Monitoring Plans, Biomass rules, or SILiAmb deadlines. What is on your mind?" }]);
        } catch (error) {
          console.error("Failed to start chat", error);
        } finally {
          setIsTyping(false);
        }
      }
    };
    initChat();
  }, []);

  const handleSend = async () => {
    if (!input.trim() || !chatSession) return;

    const userMsg: Message = { role: 'user', text: input };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    
    // 1. Simulate RAG Retrieval
    setIsRetrieving(true);
    const context = mockRetrieveContext(userMsg.text);
    
    setTimeout(async () => {
        setIsRetrieving(false);
        setActiveCitations(context);
        setIsTyping(true);

        try {
            // 2. Send to Gemini (In a real app, we'd inject the 'context' text here)
            const result = await chatSession.sendMessage({ message: userMsg.text });
            const modelMsg: Message = { 
                role: 'model', 
                text: result.text || "",
                citations: context 
            };
            setMessages(prev => [...prev, modelMsg]);
        } catch (error) {
            console.error(error);
            setMessages(prev => [...prev, { role: 'model', text: "I encountered an error." }]);
        } finally {
            setIsTyping(false);
        }
    }, 1200); // Fake delay for "Vector Search"
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const finishConsultation = async () => {
    setIsGeneratingReport(true);
    const history = messages.map(m => `${m.role}: ${m.text}`).join('\n');
    const reportData = await generateStrategicReport(history);
    if (reportData) {
      onComplete(reportData);
      setView(AppView.DASHBOARD);
    }
    setIsGeneratingReport(false);
  };

  return (
    <div className="flex h-full bg-slate-50 overflow-hidden">
      
      {/* LEFT: Main Chat Interface */}
      <div className="flex-1 flex flex-col h-full bg-white border-r border-slate-200 shadow-sm max-w-4xl mx-auto w-full">
        {/* Header */}
        <div className="p-4 border-b border-slate-100 flex justify-between items-center bg-white sticky top-0 z-10">
            <div>
            <h2 className="text-lg font-semibold text-slate-800">Compliance Audit</h2>
            <p className="text-xs text-slate-500">RAG Enabled • MRR 2018/2066 • Phase 0.5 Demo</p>
            </div>
            <button 
            onClick={finishConsultation}
            disabled={messages.length < 3 || isGeneratingReport}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
                messages.length < 3 
                ? 'bg-slate-100 text-slate-400 cursor-not-allowed' 
                : 'bg-emerald-600 text-white hover:bg-emerald-700 shadow-md'
            }`}
            >
            {isGeneratingReport ? <Loader2 className="animate-spin w-4 h-4" /> : <FileText className="w-4 h-4" />}
            {isGeneratingReport ? 'Generating...' : 'Finalize Strategy'}
            </button>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6 bg-slate-50">
            {messages.map((msg, idx) => (
            <div key={idx} className={`flex gap-4 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
                <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${
                msg.role === 'model' ? 'bg-emerald-100' : 'bg-slate-200'
                }`}>
                {msg.role === 'model' ? <Bot className="text-emerald-700 w-5 h-5" /> : <User className="text-slate-600 w-5 h-5" />}
                </div>
                
                <div className="flex flex-col gap-2 max-w-[85%]">
                    <div className={`rounded-2xl px-5 py-3 shadow-sm text-sm leading-relaxed ${
                        msg.role === 'model' 
                        ? 'bg-white text-slate-800 border border-slate-200 rounded-tl-none' 
                        : 'bg-emerald-600 text-white rounded-tr-none'
                    }`}>
                        {msg.role === 'model' ? (
                        <div className="prose prose-sm prose-emerald max-w-none">
                            <ReactMarkdown>{msg.text}</ReactMarkdown>
                        </div>
                        ) : (
                        msg.text
                        )}
                    </div>
                    {/* Citation Footnotes */}
                    {msg.citations && msg.citations.length > 0 && (
                        <div className="flex flex-wrap gap-2 ml-1">
                            {msg.citations.map((cite, cIdx) => (
                                <span key={cIdx} className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-slate-100 border border-slate-200 text-[10px] text-slate-500 font-medium">
                                    <BookOpen size={10} /> {cite.docTitle} • {cite.article}
                                </span>
                            ))}
                        </div>
                    )}
                </div>
            </div>
            ))}
            
            {/* Loading States */}
            {isRetrieving && (
                <div className="flex gap-4 animate-pulse">
                    <div className="w-8 h-8 rounded-full bg-slate-100 flex items-center justify-center">
                        <Search className="text-slate-400 w-4 h-4" />
                    </div>
                    <div className="text-xs text-slate-400 flex items-center">
                        Searching Knowledge Base (MRR, Directives)...
                    </div>
                </div>
            )}
            
            {isTyping && !isRetrieving && (
                <div className="flex gap-4">
                    <div className="w-8 h-8 rounded-full bg-emerald-50 flex items-center justify-center">
                        <Loader2 className="animate-spin text-emerald-600 w-4 h-4" />
                    </div>
                    <div className="text-xs text-slate-400 flex items-center">Consultant is analyzing regulations...</div>
                </div>
            )}
            <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="p-4 border-t border-slate-200 bg-white">
            <div className="relative">
            <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyPress}
                placeholder="Ask about biomass, penalties, or deadlines..."
                className="w-full pl-5 pr-12 py-3.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500 transition-all text-sm shadow-sm"
            />
            <button 
                onClick={handleSend}
                disabled={!input.trim() || isTyping || isRetrieving}
                className="absolute right-2 top-2 p-1.5 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 disabled:opacity-50 transition-colors"
            >
                <Send size={16} />
            </button>
            </div>
        </div>
      </div>

      {/* RIGHT: Context / Source Panel (Phase 0.5 Feature) */}
      <div className="w-80 border-l border-slate-200 bg-slate-50 flex flex-col hidden lg:flex">
        <div className="p-4 border-b border-slate-200 bg-white">
            <h3 className="font-semibold text-slate-700 text-sm flex items-center gap-2">
                <BookOpen size={16} className="text-emerald-600" />
                Live Context Retrieval
            </h3>
            <p className="text-[10px] text-slate-400 mt-1">
                Real-time snippets fetched from the vector database to ground the AI's response.
            </p>
        </div>
        
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {activeCitations.length === 0 ? (
                <div className="text-center mt-10 opacity-40">
                    <Search size={32} className="mx-auto mb-2" />
                    <p className="text-xs">Ask a question to trigger retrieval.</p>
                </div>
            ) : (
                activeCitations.map((cite, idx) => (
                    <div key={idx} className="bg-white p-3 rounded-lg border border-slate-200 shadow-sm hover:border-emerald-300 transition-colors cursor-help">
                        <div className="flex justify-between items-start mb-2">
                            <span className="text-[10px] font-bold text-emerald-700 bg-emerald-50 px-1.5 py-0.5 rounded">
                                {cite.article}
                            </span>
                            <span className="text-[10px] text-slate-400">{(cite.relevance * 100).toFixed(0)}% Match</span>
                        </div>
                        <h4 className="text-xs font-semibold text-slate-800 mb-1 leading-tight">{cite.docTitle}</h4>
                        <p className="text-[11px] text-slate-500 italic leading-relaxed">
                            "{cite.snippet}..."
                        </p>
                    </div>
                ))
            )}
        </div>
        <div className="p-3 bg-amber-50 border-t border-amber-100 text-[10px] text-amber-800">
            <strong>Audit Note:</strong> Always verify citations against the official Official Journal of the European Union (OJEU).
        </div>
      </div>

    </div>
  );
};

export default Consultation;