# Ecrã: Evidence Vault (cofre de evidências)

Código do ecrã: `COMPLIANCE` (separador "Evidence Vault") · Caminho: "Compliance Tool" → separador "Evidence Vault"

## Para que serve
Guardar os documentos de prova exigidos para a verificação e para a APA (faturas, análises, certificados), por ano de reporte. Cada documento é verificado automaticamente (OCR) quando é carregado.

## Carregar um documento ("Upload Evidence")
1. Em **"Document Type"**, escolher o tipo:
   - "Relatório de Emissões (RE)"
   - "Parecer de Verificação"
   - "Faturas de Gás Natural" (opção pré-selecionada)
   - "Análise Laboratorial (Carbonatos)": análises do teor de carbonatos da argila; devem referir a acreditação ISO 17025
   - "Certificado Calibração Balança"
   - "Certificado Sustentabilidade (RED II)": para biomassa
2. Na zona tracejada **"File (PDF, XLSX)"**, clicar em **"Click to upload"** e escolher o ficheiro. Formatos aceites: PDF, XLSX e CSV; máximo 10 MB.
3. Enquanto analisa aparece "Scanning document with AI OCR...". No fim, o documento aparece no topo da lista com o estado "Processing" ou "OCR Check Failed".

**Escolher o tipo antes de carregar:** a verificação automática procura as palavras obrigatórias desse tipo. Um tipo errado leva a "OCR Check Failed".

## Lista de documentos
- Título: "Evidence Vault (ano)" e o número de documentos.
- Colunas: "Document Name" (com versão "v1" e data de carregamento), "Type", "Status", "Actions".
- Estados ("Verified", "Processing", "OCR Check Failed", cadeado): ver o glossário.
- **"OCR Check Failed"** com "Issue: Keyword mismatch": passar o rato por cima de "Issue" mostra o texto lido. Causas habituais: tipo de documento errado, documento digitalizado com pouca qualidade, ou falta de uma referência obrigatória (ex.: ISO 17025 numa análise laboratorial). Solução: corrigir e carregar de novo com o tipo certo.

## Limitações da versão atual
- **Arrastar e largar ainda não funciona**, apesar do texto "or drag and drop". Usar o clique.
- Os botões **"Preview"** (olho) e **"Delete"** (caixote) **ainda não fazem nada**.
- O ano está fixo em 2024 e a lista começa com documentos de exemplo.
- Os documentos carregados nesta versão não ficam guardados ao sair do ecrã.
