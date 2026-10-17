# Continuidade do porte Windows — 17/10/2026

Execução individual, em fases Architect/Coder/Reviewer. Escopo: missão Windows do usuário e AGENTS.md atual. Preservar temas/mobile. Não fazer push, tag ou publicação sem autorização; não escrever o registro final antes da conclusão.

Arquitetura existente: Actions Node24 → staging nativo por hash → python-mpv → PyInstaller onedir → verificação do ZIP extraído. Retomar esse trabalho, sem reescrever componentes.

- [x] Confirmar falha histórica e runtime das Actions fixadas em `.github/workflows/windows.yml` pelos manifestos oficiais; distinguir aviso Node20 de falha libmpv.
- [x] Revisar `auralume/native.py`, `scripts/windows_native.py` e `scripts/verify_windows.py`; cobrir falhas comprovadas em `tests/test_native.py`/`tests/test_windows_packaging.py` antes de corrigir os trechos.
- [x] Rodar pytest completo e validar o build Linux relocável; preparar patch Windows isolado para preservar o trabalho fora do escopo.
- [ ] Executar pipeline nativo Windows após autorização para enviar o código; exigir testes/diagnóstico/áudio/ZIP e resolver as pendências de distribuição.
- [ ] Somente após concluir: escrever `Registros/17-10-2026.txt`, com título `17/10/2026`, mudanças e resultados reais. Até lá a pasta permanece vazia.
