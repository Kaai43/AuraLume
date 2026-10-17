# Contrato de temas Auralume v1

O contrato de intercâmbio é [auralume-theme-v1.schema.json](auralume-theme-v1.schema.json). O arquivo [theme-example.json](theme-example.json) é uma fixture válida compartilhada entre Python e Dart. `invalid/` contém entradas que ambos devem rejeitar. O identificador `$id` é apenas um identificador do schema, não uma URL a consultar em runtime.

## Regras além do JSON Schema

- UTF-8, no máximo 65.536 bytes por tema; ler no máximo limite + 1 byte antes de rejeitar um arquivo.
- Rejeitar chaves duplicadas antes de montar o mapa, JSON não finito e estrutura aninhada além da raiz e de `colors`. Não aceitar arrays, objetos extras nem QSS/scripts/URLs.
- Versão inteira exatamente 1 (booleanos não são inteiros do contrato); identificadores ASCII seguros, 1–64 caracteres. Nenhum ID é usado como caminho de arquivo.
- Nome de 1–60 pontos de código Unicode; autor opcional de 1–80; texto visível, sem controles C0/C1. Espaços nas pontas são normalizados, mas texto apenas com espaços é inválido.
- Todos os 29 tokens são obrigatórios, valores de seis dígitos hexadecimais. Canonicalizar cores em maiúsculas. Exportação desktop: chaves ordenadas, indentação de dois espaços, UTF-8, newline final. Roundtrip preserva significado.
- Presets são imutáveis. IDs ou nomes em colisão não são sobrescritos silenciosamente; a operação explícita de importar cópia cria ID/nome únicos.
- O estado de preferências do desktop (`themes_v1` no SQLite) não faz parte do intercâmbio. Tema não contém fontes, mídias, credenciais nem caminhos pessoais.

## Tokens

| Grupo | Tokens | Consumidor |
|---|---|---|
| Superfícies | background, sidebar, surface, surface_alt, player_background, menu_background | Fundos de janela, navegação, campos e controles |
| Texto | text_primary, text_secondary, text_disabled | Texto principal, auxiliar e indisponível |
| Ações | accent, accent_hover, accent_foreground, selection, focus, border | Botões, seleção, foco e limites |
| Estado | success, warning, error | Mensagens; significado também expresso em texto |
| Player | slider_track, slider_fill | Trilho e progresso |
| Cartões | card_background, card_hover | Coleções e prévias |
| Capa de fallback | cover_start, cover_middle, cover_end, cover_foreground | Gradiente e nota musical pintados pelo Auralume |
| Destaque | hero_start, hero_middle, hero_end | Gradiente da área de destaque |

Python traduz para QSS/QPalette/QPainter; Flutter traduz para Material 3. As sete cores de gradientes preservam a arte original sem carregar QSS externo. Mudança futura da lista de tokens exige uma versão nova ou migração explicitamente documentada.

Referências: [JSON Schema 2020-12](https://json-schema.org/draft/2020-12/json-schema-validation), [Qt: cascata e precedência de estilos](https://doc.qt.io/qt-6/stylesheet-syntax.html#cascading), [Qt: QPalette](https://doc.qt.io/qtforpython-6/PySide6/QtGui/QPalette.html). As validações de tamanho e chaves duplicadas pertencem ao parser, pois o schema recebe o objeto já decodificado.
