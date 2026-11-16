# Ecrã: Regulatory Lib (biblioteca regulatória)

Código do ecrã: `LIBRARY` · Menu: "Regulatory Lib" · Título no ecrã: "Regulatory Knowledge Base"

## Para que serve
Mostra a legislação carregada na base de conhecimento usada pelo AI Consultant. Se uma lei não está aqui como "Indexed", o consultor não a usa para responder.

## O que há no ecrã
- Campo **"Search regulation library..."**: filtra a lista pelo título ou pelo tipo, à medida que se escreve (ex.: "MRR", "Portuguese").
- **"Total Chunks"**: número total de pedaços indexados ("Vectors").
- Tabela com "Document Title", "Type" ("EU Directive", "Regulation", "Portuguese Law", "Guidance"), "Last Updated", "Status" ("Indexed" ou "Processing") e "Vectors" (número de pedaços).
- Documentos atuais: Diretiva 2003/87/CE (consolidada), Regulamento 2018/2066 (MRR), Regulamento 2018/2067 (AVR), Portaria n.º 256/2015 (SILiAmb) e o Guidance Document 3 sobre biomassa (ainda em "Processing").

## Limitações da versão atual
- Os botões **"Re-Index"** e **"+ Ingest New Document"** **ainda não fazem nada**. Para acrescentar legislação, contactar o administrador.
- Não é possível abrir nem ler os documentos a partir desta lista.
