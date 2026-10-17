# Windows native exception — Implementation Plan

Execução individual, por solicitação do usuário; fases Architect, Coder e Reviewer.

**Goal:** investigar exclusivamente o crash do job 117405871883 e preparar sua revalidação manual.
**Architecture:** manter DLL/binding fixados; configurar os motores Windows antes de `mpv_initialize`, sem scripts internos desnecessários. Preservar eventos, faulthandler e testes reais.
**Tech Stack:** Python 3.12 no Windows, python-mpv 1.0.8, libmpv, PySide6, pytest, Actions.
**Spec:** stack trace fornecido pelo usuário; execução 39036034661, commit 3f06a24.

- [x] Confirmar log, código LuaJIT/CPython e opções da revisão mpv 492bae0768f5e826991bf9fb222fa303371e8498.
- [x] Escrever teste real que mostre scripts Lua ainda carregados na configuração atual; executar e observar falha.
- [x] Centralizar opções Windows em `auralume/native.py`; aplicar antes da criação em `player.py` e `probe_mpv`.
- [x] Testar ciclos reais de criação/reprodução/EOF/encerramento; manter logs em falhas do Actions e executar regressão Linux.
- [x] Revisar diff, registrar evidências/limites e disponibilizar correção para execução manual, sem disparar workflow.

## Evidência e limites

DLL e criação do motor passaram no runner. A suíte abortou, sem contagem final, após mensagens SEH LuaJIT e uma access violation. CPython imprime SEH e retorna EXCEPTION_CONTINUE_SEARCH: a mensagem isolada não prova encerramento. O acesso inválido continua sem causa nativa conclusiva; desativar scripts remove uma fonte comprovada de SEH, mas só a repetição no Windows confirmará se elimina o crash observado.

Inspeção local com libmpv real demonstrou carregamento de stats, console, auto_profiles, select, positioning, commands e context_menu apesar de config/osc/ytdl desativados. `load-scripts=no` sozinho não controla os scripts internos. Inspeção estática do binário fixado (`libmpv-2.dll`) confirmou LuaJIT 2.1 e os nove scripts embutidos. Repetição com `mpv v0.41.0` (mesma versão da DLL): conjunto mínimo (`osc/ytdl/load_scripts=no`) carrega 22 scripts; conjunto completo (`native._LUA_SCRIPTS`) carrega zero. Não alterar DLL, binding ou callback simultaneamente sem evidência. Plano B (só se persistir sem LuaJIT no log): build `-Dlua=disabled -Djavascript=disabled`.

## Revisão

Conferir inicialização anterior ao primeiro script, cobertura dos dois consumidores, compatibilidade Linux sem novas opções obrigatórias, encerramento das threads, preservação do erro/exit code e ausência de publicação de binários.
