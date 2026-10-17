# Continuidade — 15/10/2026

## G0 — VERIFICADO

- Branch `main`; HEAD inicial `9d9676680fce52f1083e28df8d959279d84d936c`; árvore inicialmente limpa.
- Remoto configurado `https://github.com/Kaai43/Auralume.git`; tag local `v0.1.0`. Nenhum fetch/pull/push/checkout executado. Sincronização com remoto NÃO TESTADA; web retornou cache miss para release/run histórico.
- Commits anteriores: `15f5421` (preparação 0.1.0), `d25aa9a` (MVP). `Auralume.spec` rastreado apesar do padrão *.spec ignorado.
- Lidos AGENTS.md (local ignorado), AURALUME_WORKFLOW.md, docs/progress.md, docs/next-task.md, docs/dependencies.md, README, pyproject, spec, windows.yml, .codex/config.toml e dois arquivos .codex/agents/*.toml. Não reescritos.
- Plano anterior: `docs/superpowers/plans/2026-10-14-mvp.md`; histórico preservado. Nova ordem em `docs/plans/auralume-next-milestones.md`.
- Ambiente observado: Linux x86-64, glibc 2.43; Python venv 3.14.4; PySide6/Qt 6.12.0; mpv binding 1.0.8; pytest 9.1.1; yt-dlp 2026.8.19; mutagen 1.48.1; PyInstaller 6.22.3.
- Flutter/Dart ausentes no PATH/caminhos usuais. Java/Android SDK ausentes conforme investigação Platform. Não há projeto mobile prévio.
- Artefato Linux anterior `dist/Auralume/Auralume` presente (11.629.800 bytes do executável, sem contar _internal). Não reconstruído nem anunciado como atualizado nesta auditoria.
- Baseline sandbox: `.venv/bin/python -m pytest -q` → 57 passed, 1 error (PermissionError no socket 127.0.0.1 do teste HTTP). Repetição autorizada fora do sandbox → **58 passed in 6.25s**. Sem skip, xfail ou substituição do HTTP real.
- Dois agentes usados de verdade: `/root/themes` (luna_developer) e `/root/platform` (luna_rea, escopo atualizado). Nenhum quarto agente. Arquivos compartilhados sob posse exclusiva do coordenador.
- REA: skill consultada; fonte completa analisada por ferramentas normais como determina a skill. Investigação Spotify é histórico e não será repetida. TDD, Writing Plans, Systematic Debugging e Verification Before Completion aplicadas ao fluxo.

## Decisões e riscos

- Temas usarão settings SQLite com chave independente e escrita atômica; perfil sem configuração conserva Auralume Original. Não migrar/apagar banco real.
- Estilos locais em showEvent, pesquisa, shortcuts e QPainter impedem troca completa: G1 os centraliza.
- SDK Flutter pode ser preparado localmente sem instalação global; Java/Android ausentes impedem APK enquanto toolchain não for preparado. iOS não pode ser validado neste host Linux.
- Erro Windows histórico informado pelo usuário: 52 passed/6 failed antes de PyInstaller, libmpv não carregada. É histórico fornecido, não execução reproduzida aqui.
- Release Linux existente informada pelo usuário: AppImage e tar.gz; DEB não confirmado. Não converter ELF em PE nem publicar sem autorização.
- G1 em seguida. Windows permanece bloqueado até G3/G4 conforme protocolo; runner/publicação dependem de evidência e autorizações próprias.

## G1 — VERIFICADO

- HEAD/branch de trabalho continuam `9d9676680fce52f1083e28df8d959279d84d936c` / `main`; modificações locais aditivas e remoção do QSS fixo duplicado. Nenhum código de player/controlador/banco foi reescrito.
- Luna Themes entregou e o coordenador revisou `auralume/themes/{model,catalog,manager,style}.py`, galeria/editor e testes. Coordenador integrou app, MainWindow e CoverArt; contratos JSON e teste de integração próprios. Luna Platform preparou somente ambiente/pesquisa enquanto G1 estava aberto.
- Cinco presets, CRUD personalizado, JSON estrito/limites, import/export, colisão com cópia, persistência em settings e recuperação sem escrita ao carregar corrupção. Posição/volume/shuffle/repeat/fila/importação preservados com libmpv real e saída null.
- TDD coordenador: quatro integrações falharam antes da implementação; depois nove integrações passaram. TDD agente: módulo ausente no primeiro ciclo; verificações focadas finais 49 passed (incluindo as nove integrações).
- `.venv/bin/python -m pytest -q` com loopback autorizado → **107 passed in 7.67s**, sem skip/xfail/falhas. Baseline de 58 testes conservado, 49 novos.
- `.venv/bin/python scripts/verify_themes.py` → oito imagens renderizadas e relatório, 980×650/1240×800, original/claro/galeria/editor. Coordenador inspecionou capturas e pediu correções verificadas de contraste selecionado, foco, cantos da capa e botão circular. Paths: `docs/evidence/themes/`.
- `.venv/bin/python -m auralume --diagnostics` → Linux x86-64, frozen=false, libmpv.so.2 detectada. A prova de engine/reprodução é dos testes reais, não somente desse campo diagnóstico.
- Qt offscreen VERIFICADO; áudio audível, Windows e aparelhos mobile NÃO TESTADOS. Sem novas dependências desktop, nenhuma mídia pessoal ou mudança de licença.
- Fontes primárias consultadas: Qt QPalette, QColorDialog, stylesheet reference/syntax (links no contrato/documentação de temas).
- Decisão: avançar G2. Preparação de Windows continua bloqueada até G3.

### Atualização do inventário remoto (somente leitura)

`git ls-remote --heads --tags origin` e `git fetch --no-tags origin main` exigiram rede fora do sandbox após falha DNS. Não houve merge/checkout/push. `origin/main` real é `e8f81470b5e2e8907ad7e4adc96ff648fc67bc44`, diferente do HEAD local; a tag v0.1.0 resolve para `15f54212fce64311a7cf3983e2513d225accfc3e`. Diferenças remotas serão examinadas e preservadas ao integrar o gate correspondente.
