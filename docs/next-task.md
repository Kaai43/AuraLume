# Próxima tarefa — Windows exclusivamente

A missão Windows substitui as prioridades históricas abaixo. Trabalhar com um único agente; não restaurar workflow multiagente, retomar mobile ou desenvolver temas.

1. Ler a investigação da exceção nativa no início de `docs/windows-build.md`. Causa: LuaJIT + scripts embutidos na DLL fixada. O patch isolado antigo em `dist/windows-review/` não inclui esta correção.
2. Em 17/10/2026, o usuário autorizou enviar os fontes atuais para `main`, incluindo os trabalhos existentes, excluindo AGENTS.md, Registros e pacotes de distribuição. A validação Windows será acionada manualmente pelo usuário: Actions → Auralume Windows candidate → Run workflow, com `upload_candidate=false` enquanto a revisão de licenças estiver pendente.
3. Conferir primeiro os testes de scripts/ciclos do player e depois a suíte inteira, onedir e ZIP. Se persistir access violation **sem nenhuma linha LuaJIT no log**, seguir o plano B (build `-Dlua=disabled`) e coletar a pilha nativa antes de outra alteração. Não declarar Windows validado antes disso.
4. Concluir inventário/licenças/fontes correspondentes de libmpv/FFmpeg/Qt antes de habilitar upload de binários. Depois, obter autorização específica para disponibilizar o candidato.
5. Testar em Windows 10/11 limpo, áudio audível, dispositivos e SmartScreen; revisar o rascunho `docs/windows-release-notes.md`. Publicação exige outra aprovação explícita.

Última regressão: `130 passed`, 0 falhas/ignorados no Linux (17/10/2026), incluindo regressões da inicialização/ciclo de vida nativo e da cobertura das opções Lua. O registro local permanece ignorado pelo Git. Tags e releases continuam sem autorização. A existência dos fontes mobile não significa que o aplicativo mobile esteja pronto.

## Registro histórico anterior (não executar como prioridade atual)

O MVP 0.1.0 está implementado e empacotado em `dist/Auralume/Auralume`. **Não reiniciar** os serviços, UI ou investigação estática já registrados em `docs/progress.md`.

Próximo marco: ampliar a validação de distribuição.

1. Gerar build em Ubuntu 22.04/24.04 isolado e compatível, quando esse ambiente estiver disponível; o build atual foi produzido e validado no Ubuntu 26.04.1 x86-64.
2. Validar áudio físico PulseAudio/PipeWire e backend Wayland, preservando os testes `ao=null` e X11 já concluídos.
3. Testar URLs específicas fornecidas/autorizadas pelo usuário nas plataformas desejadas. Os testes atuais de yt-dlp e reprodução HTTP usam mídia gerada localmente.
4. Depois: exportação/importação M3U, controles de mídia MPRIS e capas embutidas. Remover plugins Qt PDF/Virtual Keyboard sem uso poderá reduzir o pacote, acompanhado de nova auditoria de dependências.

Para retomar: ler `AGENTS.md`, `AURALUME_WORKFLOW.md`, progresso e este arquivo; verificar `git status`; executar testes pertinentes. O teste HTTP e `scripts/verify_release.py` precisam de permissão para socket loopback em ambiente restrito. Não publicar nem modificar Goof Portable.
