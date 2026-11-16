# Ecrã: AI Consultant

Código do ecrã: `CONSULTATION` · Menu: "AI Consultant" · Título no ecrã: "Compliance Audit"

## Para que serve
Conversa com o consultor de IA sobre regras do CELE (biomassa, prazos, penalizações, incerteza de medição…). As respostas citam a legislação. É aqui que se fazem as perguntas regulatórias que o Guia não responde.

## O que há no ecrã
- **Conversa** (centro): o consultor apresenta-se ao abrir o ecrã. Escreve-se no campo "Ask about biomass, penalties, or deadlines..." e envia-se com Enter ou com o botão de seta.
- **Citações**: por baixo de cada resposta aparecem etiquetas com o documento e o artigo (ex.: "Regulation (EU) 2018/2066 (MRR) • Article 38").
- **Painel "Live Context Retrieval"** (direita, só em ecrãs largos): mostra os excertos da legislação usados na resposta, com a percentagem de relevância ("% Match").
- **Botão "Finalize Strategy"** (canto superior direito): gera um relatório estratégico a partir da conversa e abre o ecrã "Strategy & Data" com os resultados. Só fica ativo **a partir de 3 mensagens na conversa**. Enquanto gera, mostra "Generating...".
- Nota de auditoria (fundo do painel direito): confirmar sempre as citações no Jornal Oficial da UE.

## Mensagens de espera
- "Searching Knowledge Base (MRR, Directives)...": está a procurar na legislação.
- "Consultant is analyzing regulations...": está a preparar a resposta.

## Problemas frequentes
- **O consultor não se apresenta e as mensagens não são enviadas**: o serviço de IA do consultor não está configurado neste ambiente. Contactar o administrador da aplicação.
- **"I encountered an error."**: falha temporária; tentar de novo.
- **"Finalize Strategy" está cinzento**: a conversa ainda tem menos de 3 mensagens.

## Limitações da versão atual
- As citações são escolhidas por palavras-chave da pergunta (biomassa, prazos, incerteza/contador). Para outras perguntas aparece uma citação genérica da Diretiva 2003/87/CE. Confirmar sempre na fonte oficial.
- A conversa não fica guardada: ao sair do ecrã, perde-se.
