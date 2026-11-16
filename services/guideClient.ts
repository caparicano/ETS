// Cliente do Guia Claude: POST /api/v1/guide/chat com resposta em SSE.
// A chave da API fica no servidor; aqui só vai o token de sessão do utilizador.

export interface GuideTurn {
  role: 'user' | 'assistant';
  content: string;
}

export interface GuideScreenContext {
  ecra: string;
  titulo: string;
  elementosVisiveis: string[];
  estados: Record<string, unknown>;
}

export interface GuideHandlers {
  onText: (delta: string) => void;
  onDone?: () => void;
  onError: (message: string) => void;
}

const API_BASE: string = import.meta.env.VITE_API_URL ?? '';
export const MAX_QUESTION_CHARS = 2000;
export const MAX_HISTORY_TURNS = 40;

function authToken(): string | null {
  try {
    return localStorage.getItem('ceramets_token');
  } catch {
    return null;
  }
}

/** Divide um buffer SSE em eventos completos; devolve também o resto por processar. */
export function parseSse(buffer: string): { events: { event: string; data: any }[]; rest: string } {
  const blocks = buffer.split('\n\n');
  const rest = blocks.pop() ?? '';
  const events = [];
  for (const block of blocks) {
    let event = 'message';
    let data = '';
    for (const line of block.split('\n')) {
      if (line.startsWith('event: ')) event = line.slice(7);
      else if (line.startsWith('data: ')) data += line.slice(6);
    }
    if (!data) continue;
    try {
      events.push({ event, data: JSON.parse(data) });
    } catch {
      /* ignora blocos mal formados */
    }
  }
  return { events, rest };
}

const HTTP_ERRORS: Record<number, string> = {
  401: 'A sessão expirou. Inicie sessão novamente para usar o guia.',
  422: 'Não foi possível enviar esta pergunta. Tente uma mensagem mais curta.',
  429: 'Fez muitos pedidos ao guia. Tente novamente dentro de alguns minutos.',
  503: 'O guia ainda não está configurado neste ambiente.',
};

export async function askGuide(
  pergunta: string,
  contexto: GuideScreenContext,
  historico: GuideTurn[],
  handlers: GuideHandlers,
  signal?: AbortSignal,
): Promise<void> {
  try {
    const token = authToken();
    const res = await fetch(`${API_BASE}/api/v1/guide/chat`, {
      method: 'POST',
      signal,
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({ pergunta, contexto, historico: historico.slice(-MAX_HISTORY_TURNS) }),
    });
    if (!res.ok || !res.body) {
      handlers.onError(HTTP_ERRORS[res.status] ?? 'O guia não está disponível neste momento.');
      return;
    }
    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    for (;;) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const parsed = parseSse(buffer);
      buffer = parsed.rest;
      for (const { event, data } of parsed.events) {
        if (event === 'text') handlers.onText(data.delta);
        else if (event === 'error') handlers.onError(data.mensagem);
        else if (event === 'done') handlers.onDone?.();
      }
    }
  } catch (e) {
    if ((e as Error).name === 'AbortError') return;
    handlers.onError('Não foi possível contactar o guia. Verifique a ligação e tente novamente.');
  }
}
