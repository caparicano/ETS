# Glossário

## Siglas e termos do CELE / EU ETS
- **CELE / EU ETS**: Comércio Europeu de Licenças de Emissão (*EU Emissions Trading System*). Regime europeu em que as instalações abrangidas monitorizam as emissões de CO₂, reportam-nas e entregam licenças equivalentes.
- **EUA**: *EU Allowance*, licença de emissão. 1 EUA = 1 tonelada de CO₂.
- **Licenças gratuitas (Free Allocation)**: licenças atribuídas sem custo à instalação. Se as emissões verificadas forem superiores, a diferença tem de ser comprada.
- **tCO2**: toneladas de dióxido de carbono.
- **TEGEH**: Título de Emissão de Gases com Efeito de Estufa. A licença da instalação, emitida pela APA, que lista equipamentos e combustíveis autorizados.
- **APA**: Agência Portuguesa do Ambiente, a autoridade competente em Portugal.
- **RE**: Relatório de Emissões, o relatório anual das emissões da instalação.
- **Parecer de Verificação**: documento do verificador acreditado que confirma o RE.
- **SILiAmb**: plataforma da APA onde se submete o RE.
- **RPLE**: Registo Português de Licenças de Emissão, onde se entregam (devolvem) as licenças.
- **MRR**: Regulamento (UE) 2018/2066, sobre a monitorização e comunicação de emissões.
- **AVR**: Regulamento (UE) 2018/2067, sobre a verificação e acreditação.
- **Fluxo-fonte (source stream)**: cada combustível ou matéria-prima que gera emissões (ex.: gás natural num forno, carbonatos da argila).
- **Tier (nível)**: nível de exigência do método de monitorização (precisão das medições e dos fatores). Escolher o tier é uma decisão regulatória: encaminhar para o "AI Consultant".
- **Dados de atividade (activity data)**: a quantidade consumida no período, ex.: leitura do contador de gás em Nm³.
- **Nm³**: metro cúbico normal (volume de gás em condições normalizadas).
- **NCV / PCI**: *Net Calorific Value*, poder calorífico inferior do combustível.
- **EF**: fator de emissão (tCO₂ por unidade de energia).
- **OF**: fator de oxidação.
- **Carbonatos**: minerais da argila (ex.: CaCO₃) que libertam CO₂ na cozedura. São as "emissões de processo".
- **ISO 17025**: norma de acreditação de laboratórios. As análises laboratoriais usadas como evidência devem vir de laboratório acreditado.
- **RED II**: Diretiva das Energias Renováveis. Os certificados de sustentabilidade da biomassa seguem os seus critérios.
- **Phase 4 (ETS Phase 4)**: período atual do CELE (2021–2030).

## Termos da aplicação
- **OCR**: leitura automática do texto de um documento carregado. A aplicação verifica se o documento contém as palavras obrigatórias para o seu tipo.
- **RAG / vetores / chunks**: a forma como o AI Consultant procura na legislação. Os documentos são divididos em pedaços ("chunks"), guardados como "vectors" e pesquisados para fundamentar a resposta com citações.
- **Digital twin**: a configuração digital da instalação (equipamentos e fluxos-fonte) criada pelo "Setup New Installation".

## Estados dos documentos (Evidence Vault)
| Estado técnico | O que aparece no ecrã | Significado | O que fazer |
|---|---|---|---|
| `PENDING` | "Processing" (amarelo, a rodar) | O documento foi carregado e está a ser analisado. | Aguardar. |
| `VERIFIED` | "Verified" (verde) | O documento passou a verificação. | Nada. |
| `OCR_FAILED` | "OCR Check Failed" (vermelho) + "Issue: Keyword mismatch" | A leitura automática não encontrou palavras obrigatórias (ex.: a referência ISO 17025 numa análise de laboratório). Passar o rato por cima de "Issue" mostra o excerto lido. | Confirmar que o documento é o correto e está legível; pedir ao laboratório ou fornecedor a versão com a informação em falta e voltar a carregar. |
| `LOCKED` | Cadeado no lugar do botão de apagar | Documento bloqueado (ex.: após verificação); não pode ser apagado. | Nada; é intencional, para a auditoria. |
| `REJECTED` | (ainda sem indicação visual) | Documento rejeitado. | — |

## Estados das tarefas (Compliance Tool)
| Estado | Aparece como | Significado |
|---|---|---|
| `PENDING` | "pending" (amarelo) | Por fazer. |
| `COMPLETED` | "completed" (verde, com visto) | Concluída. |
| `OVERDUE` | "overdue" (vermelho) | Prazo ultrapassado. |

## Estados na biblioteca regulatória
- **Indexed**: documento pronto a ser usado pelo AI Consultant.
- **Processing**: documento ainda a ser processado; ainda não é usado nas respostas.
