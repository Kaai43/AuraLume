# Próxima tarefa

O MVP 0.1.0 está implementado e empacotado em `dist/Auralume/Auralume`. **Não reiniciar** os serviços, UI ou investigação estática já registrados em `docs/progress.md`.

Próximo marco: ampliar a validação de distribuição.

1. Gerar build em Ubuntu 22.04/24.04 isolado e compatível, quando esse ambiente estiver disponível; o build atual foi produzido e validado no Ubuntu 26.04.1 x86-64.
2. Validar áudio físico PulseAudio/PipeWire e backend Wayland, preservando os testes `ao=null` e X11 já concluídos.
3. Testar URLs específicas fornecidas/autorizadas pelo usuário nas plataformas desejadas. Os testes atuais de yt-dlp e reprodução HTTP usam mídia gerada localmente.
4. Depois: exportação/importação M3U, controles de mídia MPRIS e capas embutidas. Remover plugins Qt PDF/Virtual Keyboard sem uso poderá reduzir o pacote, acompanhado de nova auditoria de dependências.

Para retomar: ler `AGENTS.md`, `AURALUME_WORKFLOW.md`, progresso e este arquivo; verificar `git status`; executar testes pertinentes. O teste HTTP e `scripts/verify_release.py` precisam de permissão para socket loopback em ambiente restrito. Não publicar nem modificar Goof Portable.
