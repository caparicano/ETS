import React, { createContext, useContext, useEffect, useMemo, useState } from 'react';
import type { GuideScreenContext } from '../../services/guideClient';

const EMPTY: GuideScreenContext = { ecra: 'LANDING', titulo: '', elementosVisiveis: [], estados: {} };

interface GuideContextValue {
  screen: GuideScreenContext;
  setScreen: (ctx: GuideScreenContext) => void;
}

const Ctx = createContext<GuideContextValue>({ screen: EMPTY, setScreen: () => {} });

export const GuideProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [screen, setScreen] = useState<GuideScreenContext>(EMPTY);
  const value = useMemo(() => ({ screen, setScreen }), [screen]);
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
};

export const useGuide = () => useContext(Ctx);

/**
 * Cada ecrã declara aqui o seu contexto para o guia.
 * Enviar só estrutura e estados (contagens), nunca valores de campos ou nomes de ficheiros.
 */
export function useGuideContext(ctx: GuideScreenContext) {
  const { setScreen } = useGuide();
  const key = JSON.stringify(ctx);
  useEffect(() => {
    setScreen(JSON.parse(key));
  }, [key, setScreen]);
}
