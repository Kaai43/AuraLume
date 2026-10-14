# Progresso do Auralume

## 2026-10-14 — estado inicial verificado

- Lidos integralmente `AGENTS.md` e `AURALUME_WORKFLOW.md`.
- Ainda não havia código, testes, builds ou registros de progresso. Nada reiniciado.
- Ambiente: Ubuntu 26.04.1 x86-64, Python 3.14.4; `.venv` contém PySide6 6.12, pytest 9.1.1, PyInstaller 6.22.3, yt-dlp 2026.8.19, mpv 1.0.8 e mutagen 1.48.1. `libmpv.so.2`, mpv, FFmpeg e Xvfb disponíveis.
- Cinco skills localizadas e lidas. Dois agentes personalizados conferidos e iniciados: Luna REA investiga Spotify; Luna Developer implementa UI. Coordenador implementa serviços e integração.
- `.git` não contém repositório válido e é protegido para escrita no sandbox; nenhuma alteração publicada.
- Em andamento: MVP definido no plano; testes precederão implementação dos serviços.

## Marco 1 — serviços e integração verificados

- SQLite/favoritos/playlists/histórico/configurações; leitura local Mutagen, busca sem acentos, fila shuffle/repeat e recomendações locais implementados. Primeiro ciclo: 12 testes passaram.
- Player libmpv carregou WAV real, pausou, buscou posição, alterou volume e emitiu EOF com saída `null`; falha de arquivo ausente não gera histórico.
- UI PySide6 entregue pelo Luna Developer; controlador integra importação em segundo plano, player, persistência e preferências.
- yt-dlp API real testada contra servidor HTTP loopback com WAV próprio, sem download em disco. Socket autorizado via mecanismo de elevação após bloqueio do sandbox.
- Suíte integrada em 2026-10-14: **49 passed in 2.67s**. CLI `--diagnostics` e inicialização offscreen cobertos.
- Primeiro PyInstaller gerado; `dist/Auralume/Auralume --smoke-test` retornou `ok: true`. Captura Qt inspecionada em `docs/evidence/startup.png`.
- Revisão em andamento: corrigir atualização síncrona de preferências, melhorar fonte/layout e remover coleta acidental de libmpv/bibliotecas de sistema do bundle antes da validação final.

## Marco 2 — MVP empacotado e validado

Versão: **0.1.0**, Ubuntu **26.04.1 x86-64**. Saída: `dist/Auralume/Auralume` (onedir, aproximadamente 155 MB); mantenha `_internal` junto ao ELF.

- **58 testes passaram** na verificação final (`.venv/bin/python -m pytest -q`, 5,97 s). Cobertura: SQLite reaberto, favoritos, playlists, busca, histórico, preferências, recomendações, importação, fila e EOF reais, fontes inválidas/DRM/rede, resultados assíncronos obsoletos, encerramento durante rede, interação Qt e startup CLI.
- `scripts/verify_release.py` verificou uma cópia do ELF em outro caminho, com espaços: WAV, MP3 e FLAC carregados e registrados no histórico; yt-dlp resolveu HTTP local e libmpv reproduziu o stream, sem arquivo de áudio permanente. Relatório: `docs/evidence/release-check.json`.
- `--diagnostics` confirma `frozen: true`; executável usa Python empacotado. `--smoke-test` passou. A janela abriu na sessão gráfica Ubuntu real com `QT_QPA_PLATFORM=xcb`, salvou `desktop.png` e encerrou com `ok: true`.
- Interface revisada em capturas 1240×800 e 980×650. Corrigidos: fonte, largura de pesquisa, contexto de playlists, sincronização ao salvar preferências, arraste da posição, títulos longos e cartões. Tooltip preserva metadados completos.
- Corrigida a ordem da importação automática: varredura de pastas é determinística e autoplay mantém a fila importada. Teste de duas faixas reais chega ao fim na ordem esperada.
- Libmpv/FFmpeg e bibliotecas de sistema foram removidos do bundle via API documentada do PyInstaller. Auditoria de 184 ELF sem `not found` no host; `docs/evidence/dependencies-check.json`. O launcher `.desktop` foi verificado num diretório XDG temporário.
- Licença do código original: GPL-3.0-or-later. Avisos das dependências e inventário Qt incluídos; 28 arquivos de licença Python transitivos conferidos por SHA-256.
- Git local inicializado com autorização do mecanismo de permissões. Nenhum remoto configurado, push ou publicação executado.
- Cinco skills utilizadas: REA (chamada com provedor indisponível e fallback estático), Writing Plans, TDD, Systematic Debugging e Verification Before Completion. Os Lunas entregaram investigação/UI/auditorias; atingiram limite de uso no fechamento, concluído pelo coordenador.

### Limites de verificação

- Reprodução foi decodificada com `ao=null`; não houve confirmação auditiva em alto-falantes/fones.
- Ubuntu 22.04/24.04 e backend Wayland não foram validados. Este build é para o Ubuntu 26.04 x86-64 do host, com libmpv2 e bibliotecas gráficas do sistema.
- A integração yt-dlp foi verificada com conteúdo próprio por HTTP local. Acesso a cada plataforma externa depende de disponibilidade, formatos e autorização; nenhum acesso irrestrito ao YouTube Music é prometido.
- REA: binário Spotify confirmado e análise estática alternativa concluída; provedor pwntools-elf/Ghidra indisponível. CEF/GTK são dependências observadas; fluxos internos do player continuam desconhecidos. Original e Goof Portable não alterados.
- Capas locais de pasta e arte original de fallback; capas remotas/embutidas não são baixadas/extraídas neste MVP. Não há equalizador, MPRIS ou exportação M3U nesta versão.

## Restrições preservadas

Sem login, cobrança, serviços próprios, alterações no Goof Portable ou publicação externa. Dados locais; reprodução externa somente por URL autorizada e disponível, sem downloads permanentes.
