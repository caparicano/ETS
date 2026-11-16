# Arquitetura — Guia Claude (assistente do utilizador dentro do CeramETS)

> Estado: **S1 implementado** (esqueleto); S2–S4 por fazer · Data: 2026-11-16

## 1. Objetivo

Um painel lateral dentro do CeramETS, semelhante ao Claude no Excel ou no Chrome, que **orienta o utilizador** enquanto usa a aplicação:

- explica o ecrã onde o utilizador está e o que cada campo ou estado significa;
- responde a perguntas do tipo "como faço…?" com base no manual da aplicação;
- aponta no ecrã o botão ou campo certo (visita guiada).

### Fora de âmbito (por desenho)

- O guia **não grava, não altera e não submete nada**. Não chama nenhum serviço de domínio (cálculos, tarefas, documentos) nem a base de dados.
- Não substitui o "AI Consultant" (consultoria regulatória com RAG). Se a pergunta for regulatória de fundo, o guia encaminha o utilizador para esse ecrã.

## 2. Visão geral

```
┌──────────────────────────── Browser (React) ─────────────────────────────┐
│                                                                          │
│  Ecrãs existentes (Compliance, Evidence Vault, Wizard, Dashboard…)       │
│     │  useGuideContext({ ecra, campos, estados })                        │
│     │  data-guide-id="evidence.upload" nos elementos-chave               │
│     ▼                                                                    │
│  GuideContextProvider ──► GuidePanel (botão flutuante + painel lateral)  │
│                              │  histórico da conversa (memória da sessão) │
│                              │  destaque visual (overlay) de elementos    │
└──────────────────────────────┼───────────────────────────────────────────┘
                               │ POST /api/v1/guide/chat  (SSE / streaming)
                               ▼
┌────────────────────── FastAPI (passagem mínima) ─────────────────────────┐
│  interfaces/api/guide.py  →  domain/guide_service.py                     │
│   • guarda a ANTHROPIC_API_KEY (nunca vai para o browser)                │
│   • monta o prompt: conhecimento do guia (em cache) + contexto do ecrã   │
│   • sem acesso à BD, sem importar serviços de domínio                    │
└──────────────────────────────┬───────────────────────────────────────────┘
                               ▼
                       Claude API (Messages, streaming)
```

**Porque há uma peça no servidor?** A chave da API não pode estar no browser: hoje o `vite.config.ts` injeta a `GEMINI_API_KEY` no bundle, o que a expõe a qualquer utilizador. Esta passagem é **sem estado** e não toca nos dados do ETS.

## 3. Componentes

### 3.1 Frontend

| Ficheiro | Responsabilidade |
|---|---|
| `components/guide/GuidePanel.tsx` | Botão flutuante "Guia" + painel lateral (chat em *streaming*, Markdown com `react-markdown`, sugestões rápidas por ecrã). |
| `components/guide/GuideContext.tsx` | `GuideContextProvider` + *hook* `useGuideContext()`: cada ecrã declara o seu contexto. |
| `components/guide/Highlighter.tsx` | Overlay que realça o elemento com `data-guide-id` pedido pelo guia, com scroll até ele e uma nota curta. |
| `services/guideClient.ts` | Cliente SSE para `/api/v1/guide/chat`. |
| `guide/targets.ts` | Registo único dos `data-guide-id` válidos e da sua descrição (é a lista que o modelo pode apontar). |

**Contexto do ecrã** (enviado em cada pergunta):

```ts
{
  ecra: "EVIDENCE_VAULT",              // AppView atual
  titulo: "Evidence Vault",
  elementosVisiveis: ["evidence.upload", "evidence.type-select"],
  estados: { documentos: { PENDING: 2, OCR_FAILED: 1 } },  // contagens, não conteúdos
  passoWizard: null
}
```

Regra de privacidade: por omissão envia-se **estrutura e estados, não valores** (sem leituras de contador, nomes de ficheiros ou dados de emissões). Uma *flag* `GUIDE_SEND_FIELD_VALUES` permite ativar o envio de valores mais tarde, se for aprovado.

**Integração no layout:** `Layout.tsx` monta o `GuidePanel` uma única vez. Cada ecrã acrescenta `useGuideContext(...)` e os atributos `data-guide-id`. Não muda a lógica de nenhum ecrã.

### 3.2 Backend (passagem mínima)

| Ficheiro | Responsabilidade |
|---|---|
| `backend/interfaces/api/guide.py` | `POST /api/v1/guide/chat`, que devolve `text/event-stream`. Valida o pedido (Pydantic), aplica limites e autenticação. |
| `backend/domain/guide_service.py` | Monta o pedido ao Claude, faz o *streaming* e traduz os eventos para SSE. |
| `backend/domain/guide_knowledge.py` | Carrega e congela a base de conhecimento no arranque. |
| `docs/guia/` | Conteúdo do guia (ver 3.3). |

Contrato SSE:

```
event: text        data: {"delta": "Para carregar a fatura…"}
event: highlight   data: {"alvo": "evidence.upload", "nota": "Arraste o PDF para aqui"}
event: done        data: {"usage": {...}}
event: error       data: {"mensagem": "…"}
```

**Isolamento:** o `guide_service.py` não importa `infrastructure.database` nem serviços de `domain/`. Um teste garante isto (ver secção 8).

### 3.3 Base de conhecimento do guia

```
docs/guia/
  00-instrucoes.md          # papel, tom (PT-PT), limites, o que fazer quando não sabe
  01-glossario.md           # PENDING, VERIFIED, LOCKED, OCR_FAILED, RE, ALC, TEGEH, SILiAmb…
  ecras/
    landing.md
    consultation.md
    compliance.md
    evidence-vault.md
    setup-wizard.md
    dashboard.md
    regulatory-library.md
  fluxos/
    rotina-mensal.md        # a partir de docs/user-guides/ceramic-industry.md
    relatorio-anual.md
    acesso-verificador.md
```

O manual é pequeno (dezenas de páginas, poucas dezenas de milhares de *tokens*), por isso **não é preciso RAG nem embeddings**. Vai inteiro no *system prompt*, marcado para **prompt caching**: depois do primeiro pedido, só a pergunta e o contexto do ecrã são cobrados a preço cheio. Os `targets.ts` são exportados para JSON no *build* e entram no mesmo bloco em cache.

## 4. Pedido ao Claude

```python
client.messages.stream(
    model=settings.GUIDE_MODEL,                  # ver secção 6
    max_tokens=4000,
    output_config={"effort": "low"},             # chat de orientação: respostas rápidas
    system=[{"type": "text", "text": KNOWLEDGE, "cache_control": {"type": "ephemeral"}}],
    tools=[DESTACAR_ELEMENTO],                   # único "tool"
    messages=historico + [contexto_ecra_e_pergunta],
)
```

- **Ordem estável para a cache:** `tools` → `system` (conhecimento congelado) → `messages`. Nada volátil (datas, IDs) no `system`.
- **Ferramenta única, só visual:**
  ```json
  {
    "name": "destacar_elemento",
    "description": "Realça no ecrã do utilizador o elemento indicado. Não executa nenhuma ação.",
    "strict": true,
    "input_schema": {
      "type": "object",
      "properties": {
        "alvo": {"type": "string", "enum": ["evidence.upload", "…lista de targets.ts…"]},
        "nota": {"type": "string"}
      },
      "required": ["alvo", "nota"],
      "additionalProperties": false
    }
  }
  ```
  O backend responde logo `tool_result: "destacado"` e envia o evento `highlight` ao browser. É a única "ação" possível, e só altera o que se vê no ecrã.
- **Histórico:** fica no browser (memória da sessão), limitado às últimas ~20 trocas. O servidor não guarda conversas.
- **Recusas:** se `stop_reason == "refusal"`, mostra-se uma mensagem neutra ("Não consigo ajudar com isso aqui"). Com modelos Opus/Sonnet 5.5 ativa-se o `fallbacks: "default"` (beta `server-side-fallback-2026-07-01`).
- **Erros:** `RateLimitError` → "Tente novamente dentro de instantes"; outros erros → mensagem genérica e registo no log.

## 5. Segurança e privacidade

| Tema | Decisão |
|---|---|
| Chave API | Só no servidor (`ANTHROPIC_API_KEY`). Remover também a injeção da chave Gemini no `vite.config.ts` (risco já existente). |
| Autenticação | O endpoint exige o JWT existente (`get_current_user`). |
| Abuso e custos | Limite por utilizador (ex.: 30 pedidos/10 min), pergunta com no máximo 2 000 caracteres e `max_tokens` limitado. |
| Dados enviados | Estrutura do ecrã e estados; nunca valores, por omissão. Sem PII. |
| Injeção de instruções | O conteúdo vindo do ecrã entra como dados (`<contexto_ecra>…</contexto_ecra>`), nunca no `system`. A ferramenta só aceita alvos da lista fechada. |
| Retenção | Confirmar as condições de retenção da conta Anthropic da organização antes de produção (RGPD). |
| Auditoria | Registam-se metadados (utilizador, ecrã, *tokens*, latência), não o texto das conversas. |

## 6. Modelo — decisão em aberto

O modelo é configurável (`GUIDE_MODEL`), sem alterar código.

| Opção | Preço (entrada / saída por 1M *tokens*) | Quando faz sentido |
|---|---|---|
| `claude-opus-5-5` | $4 / $20 | Máxima qualidade nas explicações. |
| `claude-sonnet-5-5` | $2 / $10 | Equilíbrio entre qualidade e custo. |
| `claude-haiku-5-5` | $0,10 / $0,50 | Respostas curtas de orientação, com muitos utilizadores. |

Proposta: começar a avaliação (Sprint 4) com o **Haiku 5.5** e comparar com o Sonnet 5.5 em ~30 perguntas reais. A escolha final é do produto.

## 7. Fluxo de uma pergunta

1. O utilizador está no Evidence Vault e escreve "como carrego a fatura do gás?".
2. O `GuidePanel` junta o contexto do ecrã e o histórico e faz `POST /api/v1/guide/chat`.
3. O FastAPI valida o JWT e os limites, e abre o *stream* com o Claude (conhecimento servido da cache).
4. O Claude responde com o passo a passo e chama `destacar_elemento({alvo: "evidence.type-select"})`.
5. O browser mostra o texto à medida que chega e realça a lista "Tipo de documento".
6. Nada foi gravado. O ETS continua exatamente no mesmo estado.

## 8. Testes

- **Isolamento:** um teste falha se `guide_service.py` importar a BD ou serviços de domínio.
- **Contrato SSE:** testes com o cliente Anthropic simulado (*mock*), no estilo dos testes atuais em `backend/tests`.
- **Alvos:** todos os `data-guide-id` do `enum` existem no código dos ecrãs (verificação no *build*).
- **Qualidade:** conjunto de ~30 perguntas por ecrã com a resposta esperada, corrido antes de cada alteração ao manual ou ao modelo.

## 9. Plano de implementação

| Sprint | Âmbito | Motor recomendado |
|---|---|---|
| **S1 — Esqueleto** | `guide.py` + `guide_service.py` com *streaming* SSE, `GuidePanel` no `Layout`, autenticação e limites, e remoção da chave do bundle | **Sonnet 5.5** |
| **S2 — Conhecimento e contexto** | `docs/guia/` (instruções, glossário, um ficheiro por ecrã), `useGuideContext` em todos os ecrãs, prompt caching | **Sonnet 5.5** (redação do manual revista por quem conhece o ETS) |
| **S3 — Visita guiada** | `targets.ts`, `data-guide-id`, ferramenta `destacar_elemento`, `Highlighter` | **Sonnet 5.5** |
| **S4 — Avaliação e afinação** | Conjunto de perguntas, comparação Haiku vs Sonnet, custos, revisão de segurança e privacidade | **Opus 5.5** |

## 10. Estado de implementação

**S1 (feito):**
- Backend: `POST /api/v1/guide/chat` (SSE), `guide_service.py`, `guide_knowledge.py`, `guide_limits.py` e `docs/guia/00-instrucoes.md`. Autenticação com o JWT existente, limite de 30 pedidos por 10 minutos por utilizador (configurável: `GUIDE_RATE_MAX`, `GUIDE_RATE_WINDOW_SECONDS`), validação de tamanhos e erro 503 se faltar a `ANTHROPIC_API_KEY`.
- Modelo por omissão: `claude-haiku-5-5` (variável `GUIDE_MODEL`), com `effort: low`.
- Frontend: `GuidePanel`, `GuideContext`, `services/guideClient.ts`, montados no `Layout`; proxy `/api` no Vite. O token de sessão é lido de `localStorage["ceramets_token"]` (ainda não existe login no frontend).
- Testes: `backend/tests/test_guide.py` (18 testes, incluindo o de isolamento) e verificação no browser com Playwright.

**Não incluído no S1, de propósito:**
- **Remoção da chave Gemini do bundle.** O ecrã *AI Consultant* ainda chama o Gemini diretamente do browser (`services/geminiService.ts`); remover a chave deixaria esse ecrã sem funcionar. Fica para quando o AI Consultant passar a usar o backend.
- **Fallback de recusa (`fallbacks`)** e **cache real do manual:** o manual atual é curto e fica abaixo do mínimo cacheável; passa a contar quando o S2 o encher. Valida-se `usage.cache_read_input_tokens` no S4.
- **Teste com a API real:** nesta sessão não havia chave, por isso o cliente Claude foi simulado nos testes. Falta um pedido real antes de produção.

## 11. Decisões pendentes

1. Modelo do guia em produção (secção 6).
2. Se o guia pode ver os **valores** dos campos ou só a estrutura (secção 5).
3. Língua das respostas: PT-PT fixo, ou acompanhar a língua do utilizador. A interface está hoje em inglês.
4. Quem escreve e valida o conteúdo de `docs/guia/` (é o que mais determina a qualidade do guia).
