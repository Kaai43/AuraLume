# Auralume — Implementation Plan G0–G5

> Execução: coordenador Codex e exatamente dois agentes existentes, Luna Developer/Themes e Luna REA reaproveitado como Platform/Flutter. A autorização executiva do usuário dispensa nova aprovação deste plano; não criar agentes adicionais.

**Goal:** acrescentar temas desktop e uma fundação Flutter verificável ao MVP existente, estabilizar Linux e preparar Windows por último.

**Architecture:** manter serviços Python/Qt, player e SQLite. Temas são valores validados, persistidos num registro settings e traduzidos para QSS/QPalette; o JSON v1 é o contrato compartilhado com Dart, sem QSS intercambiável. Flutter é um projeto independente com contratos de domínio e shell demonstrativo honesto.

**Tech Stack:** Python >=3.12, PySide6/Qt6, libmpv, SQLite, pytest; Flutter/Dart oficial local para a fundação mobile.

**Spec:** protocolo mestre G0–G5 fornecido pelo usuário em 2026-10-15 e `AURALUME_WORKFLOW.md`. O protocolo novo substitui apenas a ordem de trabalho: MVP e investigação Spotify permanecem histórico concluído.

## Restrições globais

- Não reiniciar código existente. Preservar GPL-3.0-or-later, dados e publicações anteriores.
- Nenhum push, alteração de tags/releases ou upload público sem autorização expressa.
- Windows: somente leitura antes de G4; build nativo/candidato somente em G5 após gates anteriores.
- Não silenciar falhas com skip/xfail, mocks de integração ou continue-on-error.
- Áudio null não comprova áudio físico; Flutter widget tests não comprovam aparelho real.
- Build/release Linux existente não é um DEB confirmado nem um executável Windows.

## Revisão prioritária

- Temas hostis: limites UTF-8/64 KiB, estrutura, duplicatas, IDs e chaves desconhecidas.
- Perfil antigo/corrompido: conservar biblioteca, preferências e temas recuperáveis; fallback original com aviso.
- Troca durante reprodução/importação: engine, fila, posição, volume, repeat e shuffle preservados.
- Widgets dinâmicos/dialogs/QPainter: atualizar cores realmente renderizadas e testar teclado/telas pequenas.
- Contrato Dart/Python: aceitar as mesmas fixtures, sem compartilhar caminhos ou abrir o DB desktop no celular.

## G0 — inventário

- [x] Ler instruções/workflow/progresso/próxima tarefa e configuração dos dois agentes.
- [x] Auditar Git, testes, ambiente, UI, persistência e artefatos existentes.
- [x] Baseline: `.venv/bin/python -m pytest -q` → 58 passed após permitir loopback.
- [x] Registrar inventário em `docs/progress/continuity-2026-10.md`.

## G1 — temas

**Posse A:** `auralume/themes/**`, `auralume/ui/theme_dialog.py`, `tests/test_themes*.py` exceto integração.
**Posse coordenador:** `main_window.py`, `widgets.py`, `app.py`, `docs/contracts/**`, `tests/test_themes_integration.py`, documentação compartilhada.

**Interfaces:** `ThemeDefinition(id, name, colors, author=None)`, JSON schema_version=1; `ThemeManager(settings=None)` consome get_setting/set_setting e fornece active_theme, themes(), set_active(id), save(theme), duplicate(id,name), rename(id,name), delete(id), import_json(data, conflict='reject'), export_json(id), theme_changed(ThemeDefinition), warning. Estado persistido numa única chave `themes_v1`, sem migração SQL. `stylesheet(theme)`/`palette(theme)` centralizam visual. `ThemeGalleryDialog(manager,parent)` oferece edição e aplicação explícita. `MainWindow(theme_manager=...)` aplica antes de show().

- [ ] Testes vermelhos de parser, limites, presets, conflitos, roundtrip e settings reaberto/legado.
- [ ] Implementar modelo imutável, cinco presets, serialização e operações transacionais.
- [ ] Testes Qt vermelhos de preview isolado, cancelamento/salvamento/aplicação e CRUD.
- [ ] Implementar galeria/editor com nomes, cores, import/export e confirmação de exclusão.
- [ ] Testes de integração vermelhos: estilo real/cover/dialogs, navegação e mpv real preservado.
- [ ] Integrar sem reconstruir serviços; eliminar estilos de cor locais sobrepostos.
- [ ] Executar testes e revisar capturas 980×650/1240×800, claro/escuro/editor.
- [ ] Atualizar evidência e revisar diff antes de declarar gate.

## G2 — fundação Flutter

**Posse B:** `mobile/auralume_mobile/**`, `docs/mobile-architecture.md`, ADR mobile. Sem acesso de escrita ao desktop.

- [ ] Preparar SDK stable oficial em diretório local ignorado; registrar versão/hash, doctor e limitações. Sem sudo.
- [ ] Após G1, gerar template oficial CLI com Android/iOS, identificador provisório documentado.
- [ ] Testes vermelhos de domínio, JSON compartilhado, navegação e estados vazios.
- [ ] Implementar Track/Playlist/PlaybackState/ThemeDefinition e interfaces de biblioteca/player/playlists/temas.
- [ ] Implementar Material 3 e telas navegáveis; áudio indisponível claramente indicado.
- [ ] `flutter pub get`; `dart format --output=none --set-exit-if-changed .`; `flutter analyze`; `flutter test`.
- [ ] Build Android somente com toolchain disponível. iOS fica para macOS/Xcode.

## G3 — estabilização

- [ ] Revisar diffs dos dois agentes e testar fixtures válidas/inválidas nos dois parsers.
- [ ] Suíte Python completa sem redução; Flutter checks; smoke Linux/dados temporários Unicode/espaços.
- [ ] Capturas renderizadas inspecionadas e, se acessível, sessão gráfica real.
- [ ] Documentar temas/mobile/licenças/limites; verificar Git, recursos, caches e `git diff --check`.
- [ ] Congelar escopo funcional desktop/mobile.

## G4 — portabilidade Windows

**Posse coordenador:** `player.py`, `diagnostics.py`, `app.py`, `Auralume.spec`, `.github/workflows/*`, testes relacionados e `docs/windows-build.md`.

- [ ] Reexaminar falha histórica: testes/libmpv antes de PyInstaller, sem presumir causa nova.
- [ ] Comparar fonte oficial mpv/shinchiro/MSYS2; fixar URL/versão/x64/SHA-256 e auditar licenças/transitivas.
- [ ] Testes vermelhos de descoberta inicial de DLL, diagnóstico real, dados Windows e bundle.
- [ ] Implementar carregamento antes do binding, diretórios seguros e handles duráveis; preservar Linux/XDG.
- [ ] Preparar CI manual com testes integrais, build onedir, WAV próprio, ZIP extraído Unicode e manifesto.
- [ ] Regressão Linux e relatório de limites; não afirmar execução Windows sem runner.

## G5 — última etapa

- [ ] Obter autorização apenas se execução exigir push/ação remota ainda não autorizada; preparar diff revisável antes.
- [ ] Executar runner Windows x64, testes, build e validação fora de source/build.
- [ ] Auditar pacote/dependências/licenças e produzir manifesto e release notes em inglês.
- [ ] Comparar asset em v0.1.0 com nova versão: alterações funcionais exigem código/tag correspondentes, sem mover tags.
- [ ] Oferecer candidato interno e registrar testes manuais Windows/áudio/SmartScreen ainda necessários.
- [ ] Publicação é ação separada após aprovação expressa; não iniciar recursos novos depois da proposta.
