# Ecrã: Setup New Installation (assistente de configuração)

Código do ecrã: `DASHBOARD` (janela sobre o ecrã) · Caminho: "Strategy & Data" → "Setup New Installation" · Título: "AI Setup Wizard"

## Para que serve
Configurar a instalação (equipamentos e fluxos-fonte) a partir do TEGEH, numa conversa guiada. O resultado é o plano de monitorização e o "digital twin" da instalação.

## Passos
1. **Carregar o TEGEH**: em "Upload TEGEH Permit", clicar em **"Select PDF File"** e escolher o PDF do título. Só aceita PDF.
2. **Conversa**: o assistente lista os equipamentos que encontrou (ex.: fornos, atomizadores) e pergunta se estão corretos. Depois pergunta pelo combustível principal de cada equipamento. Responder no campo "Type your answer..." e enviar com Enter ou com a seta. Enquanto pensa mostra "Analyzing...".
3. **Pré-visualização ("Configuration Ready")**: mostra o nome da instalação e cada fluxo-fonte com o método ("Method: Standard • Tier X") e o combustível.
   - **"Back to Edit"**: volta à conversa para corrigir.
   - **"Approve & Create"**: aprova e cria a configuração.
4. **"Exit"** (canto superior direito): sai sem criar nada.

## Dicas
- Antes de aprovar, confirmar que todos os equipamentos e combustíveis do TEGEH estão na pré-visualização.
- O tier proposto é uma sugestão. A escolha final deve seguir o plano de monitorização aprovado pela APA.

## Limitações da versão atual
- É uma **demonstração**: o assistente usa respostas de exemplo (instalação "Cerâmica Leiria") seja qual for o PDF carregado.
- Nesta versão entende respostas em inglês: responder **"yes"** para confirmar os equipamentos e indicar o combustível com a palavra **"gas"** (ex.: "natural gas"). Outras respostas dão "Could you clarify?".
- "Approve & Create" fecha o assistente, mas a configuração ainda não aparece noutros ecrãs.
