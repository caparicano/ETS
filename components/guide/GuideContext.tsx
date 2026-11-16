import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import type { GuideScreenContext } from '../../services/guideClient';

/** Limite de caracteres do JSON de estados (o backend recusa acima de 8000). */
export const MAX_STATE_CHARS = 7000;

interface GuideContextValue {
  screen: GuideScreenContext;
  setBase: (ecra: string, titulo: string) => void;
  setSection: (key: string, data: unknown) => void;
  removeSection: (key: string) => void;
}

const Ctx = createContext<GuideContextValue>({
  screen: { ecra: 'LANDING', titulo: '', elementosVisiveis: [], estados: {} },
  setBase: () => {},
  setSection: () => {},
  removeSection: () => {},
});

/** Corta textos longos e listas grandes para o contexto caber no limite. */
export function compact(value: unknown, depth = 0): unknown {
  if (typeof value === 'string') return value.length > 200 ? value.slice(0, 200) + '…' : value;
  if (Array.isArray(value)) return value.slice(0, 20).map((v) => compact(v, depth + 1));
  if (value && typeof value === 'object' && depth < 4) {
    return Object.fromEntries(Object.entries(value).map(([k, v]) => [k, compact(v, depth + 1)]));
  }
  return value;
}

export const GuideProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [base, setBaseState] = useState({ ecra: 'LANDING', titulo: '' });
  const [sections, setSections] = useState<Record<string, unknown>>({});

  const setBase = useCallback((ecra: string, titulo: string) => setBaseState({ ecra, titulo }), []);
  const setSection = useCallback((key: string, data: unknown) => setSections((s) => ({ ...s, [key]: data })), []);
  const removeSection = useCallback(
    (key: string) =>
      setSections((s) => {
        const { [key]: _removed, ...rest } = s;
        return rest;
      }),
    [],
  );

  const screen = useMemo<GuideScreenContext>(() => {
    let estados = compact(sections) as Record<string, unknown>;
    if (JSON.stringify(estados).length > MAX_STATE_CHARS) {
      estados = { aviso: 'contexto demasiado grande; só as secções principais', secoes: Object.keys(sections) };
    }
    return { ...base, elementosVisiveis: [], estados };
  }, [base, sections]);

  const value = useMemo(() => ({ screen, setBase, setSection, removeSection }), [screen, setBase, setSection, removeSection]);
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
};

export const useGuide = () => useContext(Ctx);

/** Declara o ecrã atual (usado pelo Layout). */
export function useGuideScreen(ecra: string, titulo: string) {
  const { setBase } = useGuide();
  useEffect(() => {
    setBase(ecra, titulo);
  }, [ecra, titulo, setBase]);
}

/**
 * Um componente declara o que o utilizador está a ver, incluindo valores.
 * A secção é removida quando o componente sai do ecrã.
 */
export function useGuideSection(key: string, data: unknown) {
  const { setSection, removeSection } = useGuide();
  const json = JSON.stringify(data ?? null);
  useEffect(() => {
    setSection(key, JSON.parse(json));
  }, [key, json, setSection]);
  useEffect(() => {
    return () => removeSection(key);
  }, [key, removeSection]);
}
