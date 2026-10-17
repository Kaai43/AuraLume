# Temas desktop

Abra **Temas**, abaixo de Configurações. Há cinco presets imutáveis: Auralume Original, Midnight Blue, Rose Velvet, Forest e Soft Daylight. A lista marca o tema em uso com o texto **Ativo**. Auralume Original permanece como padrão em perfis anteriores.

Selecionar uma opção mostra sua prévia. **Aplicar tema** confirma a troca. A janela, o player, a fila, o controlador e o banco permanecem abertos.

**Criar meu tema** e **Duplicar** usam o tema selecionado como ponto de partida. No editor, informe o nome, altere os códigos `#RRGGBB` ou use o seletor de cores. A prévia é independente da janela principal. **Redefinir** restaura o rascunho inicial; **Cancelar** o descarta. **Salvar** guarda o tema; **Aplicar** o guarda e seleciona. Ao editar um tema que já está ativo, salvar atualiza sua aparência após a confirmação.

Temas personalizados podem ser editados, renomeados, duplicados e excluídos. Excluir exige confirmação e nunca apaga música. Se o tema em uso for excluído, a seleção volta ao Auralume Original. Os presets não podem ser alterados ou excluídos.

**Exportar** grava JSON; **Importar** valida o conteúdo antes de salvar. Uma colisão de nome ou identificador oferece importar uma cópia com identidade nova, sem substituir o existente. Campos extras, valores que não são cores, JSON inválido ou arquivos acima de 64 KiB são rejeitados. Tema não executa código nem consulta URLs.

Os temas e a seleção ficam na chave `themes_v1` da tabela `settings` do mesmo banco da biblioteca. `--data-dir` também determina onde essa configuração é guardada. Não há migração de esquema SQL. Carregar um estado corrompido não o sobrescreve automaticamente; o aplicativo informa a recuperação, conserva os temas válidos recuperáveis e usa Original quando a seleção não pode ser recuperada.

O editor informa contraste das combinações avaliadas, com alvo 4,5:1. Uma cor personalizada ainda pode produzir combinações pouco legíveis; o aviso não equivale a uma certificação de acessibilidade. O contrato e os 29 tokens estão em [contracts/README.md](contracts/README.md). QSS e recursos externos não fazem parte do arquivo.

Verificação reproduzível:

```bash
.venv/bin/python -m pytest -q tests/test_themes_model.py tests/test_themes_manager.py tests/test_themes_style.py tests/test_themes_dialog.py tests/test_themes_integration.py
.venv/bin/python scripts/verify_themes.py
```

As capturas renderizadas ficam em `docs/evidence/themes/`; `render-report.json` registra dimensões/backend. Contagens e limites de verificação estão no [registro de continuidade](progress/continuity-2026-10.md). Captura offscreen demonstra renderização; não comprova áudio físico nem comportamento de outro sistema operacional.
