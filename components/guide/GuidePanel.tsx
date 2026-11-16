import React, { useEffect, useRef, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { BookOpenCheck, Loader2, Send, X } from 'lucide-react';
import { askGuide, GuideTurn, MAX_QUESTION_CHARS } from '../../services/guideClient';
import { useGuide } from './GuideContext';

const SUGGESTIONS: Record<string, string[]> = {
  DEFAULT: ['O que posso fazer neste ecrã?', 'Explica-me os termos que aparecem aqui.'],
  COMPLIANCE: ['Como carrego uma fatura de gás natural?', 'O que significa OCR_FAILED?'],
  DASHBOARD: ['Como leio este painel?'],
  CONSULTATION: ['Como funciona o AI Consultant?'],
  LIBRARY: ['Como pesquiso na biblioteca regulatória?'],
};

const GuidePanel: React.FC = () => {
  const { screen } = useGuide();
  const [open, setOpen] = useState(false);
  const [turns, setTurns] = useState<GuideTurn[]>([]);
  const [input, setInput] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [turns, error]);
  useEffect(() => {
    return () => abortRef.current?.abort();
  }, []);

  const send = async (text: string) => {
    const pergunta = text.trim().slice(0, MAX_QUESTION_CHARS);
    if (!pergunta || busy) return;
    const historico = turns;
    setTurns([...historico, { role: 'user', content: pergunta }, { role: 'assistant', content: '' }]);
    setInput('');
    setError(null);
    setBusy(true);
    abortRef.current = new AbortController();
    await askGuide(
      pergunta,
      screen,
      historico,
      {
        onText: (delta) =>
          setTurns((t) => {
            const copy = [...t];
            const last = copy[copy.length - 1];
            copy[copy.length - 1] = { ...last, content: last.content + delta };
            return copy;
          }),
        onError: (m) => setError(m),
      },
      abortRef.current.signal,
    );
    // remove resposta vazia se falhou
    setTurns((t) => (t.length && t[t.length - 1].role === 'assistant' && !t[t.length - 1].content ? t.slice(0, -1) : t));
    setBusy(false);
  };

  const suggestions = SUGGESTIONS[screen.ecra] ?? SUGGESTIONS.DEFAULT;

  return (
    <>
      {!open && (
        <button
          onClick={() => setOpen(true)}
          className="fixed bottom-6 right-6 z-40 flex items-center gap-2 bg-emerald-600 text-white px-4 py-3 rounded-full shadow-lg hover:bg-emerald-700 transition-colors"
          aria-label="Abrir guia"
        >
          <BookOpenCheck size={20} />
          <span className="font-medium">Guia</span>
        </button>
      )}
      {open && (
        <aside
          className="fixed top-0 right-0 z-40 h-full w-full sm:w-96 bg-white border-l border-slate-200 shadow-2xl flex flex-col"
          aria-label="Guia CeramETS"
        >
          <header className="flex items-center justify-between px-4 py-3 border-b border-slate-100">
            <div>
              <h2 className="font-bold text-slate-800 flex items-center gap-2">
                <BookOpenCheck size={18} className="text-emerald-600" /> Guia CeramETS
              </h2>
              <p className="text-xs text-slate-400">Explica e orienta. Não altera dados.</p>
            </div>
            <button onClick={() => setOpen(false)} className="p-1 text-slate-400 hover:text-slate-700" aria-label="Fechar guia">
              <X size={20} />
            </button>
          </header>

          <div className="flex-1 overflow-y-auto p-4 space-y-3">
            {turns.length === 0 && (
              <div className="space-y-2">
                <p className="text-sm text-slate-500">
                  Estou a ver o ecrã <strong>{screen.titulo || screen.ecra}</strong>. Pergunte-me como fazer algo ou o que
                  significa um termo.
                </p>
                {suggestions.map((s) => (
                  <button
                    key={s}
                    onClick={() => send(s)}
                    className="block w-full text-left text-sm px-3 py-2 border border-slate-200 rounded-lg text-slate-600 hover:bg-slate-50"
                  >
                    {s}
                  </button>
                ))}
              </div>
            )}
            {turns.map((t, i) => (
              <div key={i} className={t.role === 'user' ? 'flex justify-end' : 'flex justify-start'}>
                <div
                  className={`max-w-[90%] rounded-xl px-3 py-2 text-sm ${
                    t.role === 'user' ? 'bg-emerald-600 text-white' : 'bg-slate-100 text-slate-800'
                  }`}
                >
                  {t.role === 'assistant' ? (
                    t.content ? (
                      <div className="prose prose-sm max-w-none">
                        <ReactMarkdown>{t.content}</ReactMarkdown>
                      </div>
                    ) : (
                      <Loader2 size={16} className="animate-spin text-slate-400" />
                    )
                  ) : (
                    t.content
                  )}
                </div>
              </div>
            ))}
            {error && <p className="text-sm text-red-600 bg-red-50 rounded-lg px-3 py-2">{error}</p>}
            <div ref={endRef} />
          </div>

          <form
            onSubmit={(e) => {
              e.preventDefault();
              send(input);
            }}
            className="p-3 border-t border-slate-100 flex gap-2"
          >
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              maxLength={MAX_QUESTION_CHARS}
              placeholder="Pergunte ao guia…"
              className="flex-1 text-sm border border-slate-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-emerald-500"
            />
            <button
              type="submit"
              disabled={busy || !input.trim()}
              className="bg-emerald-600 text-white p-2 rounded-lg disabled:opacity-40"
              aria-label="Enviar"
            >
              <Send size={18} />
            </button>
          </form>
        </aside>
      )}
    </>
  );
};

export default GuidePanel;
