# Verificação da interface — 2026-10-14

UI PySide6 integrada ao controlador, SQLite e libmpv. Capturas renderizadas e inspecionadas:

- `evidence/desktop.png`: **executável** aberto na sessão gráfica Ubuntu real (X11/xcb), com dados temporários; inicialização e encerramento passaram.
- `evidence/player.png`: executável relocacionado reproduzindo MP3 de teste; metadados lidos do arquivo, `ao=null`.
- `evidence/recommendations.png` e `evidence/playlists.png`: aplicação integrada offscreen, 1240×800, SQLite temporário e WAVs/metadados fictícios criados só para demonstração. Não representam catálogo externo ou biblioteca pessoal.
- `evidence/long-titles.png`: 980×650, nomes muito longos; controles do player permanecem visíveis, cartões e tabela abreviam texto e tooltips expõem o valor completo.

Problemas reproduzidos e corrigidos: sobrescrita síncrona dos campos ao salvar preferências, metadados longos expandindo labels/cards, artista excessivamente largo na tabela, navegação indevida em `show_tracks`, fila abrindo modal ao atualizar dados e slider mudando durante arraste. Os comportamentos críticos têm testes de UI/integrados.

As capturas confirmam composição e renderização; não equivalem a uma sessão longa de uso manual. Não houve confirmação auditiva física; reprodução automatizada usa saída nula. Wayland e leitores de tela não foram exercitados.
