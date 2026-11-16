# Ecrã: Compliance Tool

Código do ecrã: `COMPLIANCE` · Menu: "Compliance Tool" · Título no ecrã: "Compliance Manager (Portugal)"

## Para que serve
Centro do trabalho de conformidade: tarefas com prazos, registo mensal de consumos e cofre de documentos de prova.

## Zonas do ecrã
1. **"Active Sector"** (topo): lista para escolher o setor: "Cerâmica (ex: Tijolos & Telhas)" ou "Agro-Alimentar (ex: Sugal / Tomate)". No setor agro-alimentar aparece "Campaign Status: OFF-SEASON" (estado da campanha do tomate).
2. **"Next Major Deadline"** (canto superior direito): data do próximo prazo e "days remaining". Fica a laranja quando faltam menos de 30 dias e a verde nos outros casos. Se o número for negativo, o prazo já passou.
3. **Barra de etapas**: "Data Collection" → "SILiAmb Submission" → "Verification" → "RPLE Surrender". A etapa atual está a verde.
4. **Separadores**: "Pending Tasks" (tarefas) e "Evidence Vault" (documentos; ver o manual próprio).
5. **"AI Auditor"** (coluna direita): indica quantas tarefas estão a ser acompanhadas.

## Separador "Pending Tasks"
Cada linha mostra o título, a data limite ("Due"), a categoria e o estado.
- Categorias: **Data** (inserir dados), **Admin** (ex.: obter o Parecer de Verificação), **Compliance** (ex.: submeter o RE no SILiAmb), **Surrender** (entregar licenças no RPLE).
- Estados: "pending", "completed", "overdue" (ver glossário).
- **Tarefas de registo mensal** (ex.: "Registo Mensal: Gás Natural (Janeiro)") têm um contorno verde: **são as únicas que abrem ao clicar**. Abrem o formulário de registo (ver abaixo).
- As restantes tarefas (verificação, RE, RPLE) **ainda não abrem nada ao clicar**. São lembretes de prazo; o trabalho faz-se fora da aplicação (SILiAmb, RPLE, verificador).

## Formulário de registo mensal (janela sobre o ecrã)
Abre ao clicar numa tarefa de registo mensal.
- Cabeçalho: nome da tarefa e "Task ID".
- Bloco verde: nome do fluxo-fonte (ex.: "Natural Gas Combustion Line 1") e o método configurado (ex.: "Standard Tier 2 (MRR Annex VI)").
- Campo **"Meter Reading (Consumo)"** (obrigatório, assinalado com *): o consumo total de gás natural do período em **Nm³**, tal como na fatura ou no contador. Só aceita números ≥ 0.
- Botão **"Calculate & Submit Entry"**: calcula as emissões (tCO₂ = consumo × NCV × EF × OF × 0,001) e submete o registo. Durante o cálculo mostra "Calculating...".
- **"Close"** (acima da janela, à direita): fecha sem submeter.

Depois de submeter, a janela fecha e volta-se à lista de tarefas.

### Dúvidas comuns no formulário
- *Que valor ponho?* O consumo do mês em Nm³. Se a fatura vier em kWh, é preciso o fator de conversão do fornecedor; em caso de dúvida, confirmar com o fornecedor de gás ou no AI Consultant.
- *Posso pôr vírgula decimal?* O campo é numérico; o browser decide se aceita vírgula ou ponto. Se não aceitar a vírgula, usar ponto.
- *Que fatores são usados?* Os fatores configurados para o fluxo-fonte (NCV e EF). Escolher fatores e tiers é uma decisão regulatória: AI Consultant ou verificador.

## Limitações da versão atual
- As tarefas e prazos mostrados são **dados de exemplo** e não mudam com o setor escolhido.
- O período do registo mensal está fixo (janeiro de 2025) nesta versão.
- O resultado do cálculo não fica visível depois de submeter, porque a janela fecha logo.
