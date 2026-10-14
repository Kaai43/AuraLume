# Investigação estática do Spotify para Linux

Data: 2026-10-14

Escopo: somente `/snap/spotify/current/usr/share/spotify/spotify`; nenhum outro arquivo do pacote foi consultado e o executável não foi iniciado nem alterado.

## Identidade e método

`stat` confirmou que o arquivo existe e pode ser lido (59.769.496 bytes). `file` identificou ELF64 little-endian, x86-64, PIE (`ET_DYN`), dinamicamente ligado, com interpretador `/lib64/ld-linux-x86-64.so.2`, Build ID `50127278266f572a0effb43db6e70e0d16c25ccb`. SHA-256 observado: `81fe35f3e09ce47b1b1c573eb32d680cafda870132e344c7185a881cdb927544`.

O provedor REA recomendado para layout ELF foi tentado com `inspect_binary_layout`, `detail: summary`. A chamada retornou `provider_unavailable`: `pwntools-elf` requer Python com pwntools 4.15.0, pyelftools 0.33 e Unicorn 2.1.2. O Python do `.venv` não tem esses três pacotes instalados. Ghidra também não está disponível como comando. Nenhum componente foi instalado. Não havia `docs/reverse-engineering.md` ou outra investigação em `docs/` antes desta execução.

Como alternativa estática, foram usados `file`, `sha256sum`, `readelf` (`-h`, `-l`, `-d`, `--dyn-syms`) e `strings` com busca limitada a nomes de tecnologias, funções CEF, rotas e termos de acessibilidade. `objdump`, `nm`, `ldd` e `gdb` estão instalados, mas não foram necessários; em particular, `ldd` não foi usado. Não houve execução do Spotify, depuração, acesso de rede ou inspeção de outros componentes do Snap. Como o provedor REA não iniciou, não existe Evidence ID REA nesta rodada; as evidências abaixo são as saídas locais dos comandos indicados.

## Evidências e conclusões

| Pergunta | Observação estática | Conclusão e confiança |
|---|---|---|
| Formato e arquitetura | ELF PIE `ET_DYN`, 64-bit, little-endian, `EM_X86_64`; carregamento dinâmico. | **Observado:** cliente nativo x86-64 com endereço de carga variável. Não identifica por si só a linguagem do produto. |
| Interface e bibliotecas | `DT_NEEDED` inclui `libcef.so`, GTK 3 (`libgtk-3`, `libgdk-3`), GLib/GIO/GObject, Pango, HarfBuzz, ATK, Cairo, X11, Ayatana AppIndicator e DBusMenu. A busca em strings encontrou nomes de funções CEF como `cef_execute_process`, `cef_initialize` e `cef_run_message_loop`. | **Observado:** dependência do Chromium Embedded Framework e bibliotecas GTK/Linux no executável. **Inferência:** a aplicação provavelmente hospeda uma interface web via CEF e usa GTK para integração nativa, incluindo indicador de área de notificação. Isto não prova que seja Electron nem que toda a interface use web. |
| Inicialização | Nomes de funções CEF de subprocesso, inicialização e loop principal aparecem como strings; o ELF depende de `libcef.so`. | **Observado:** há nomes associados ao ciclo de vida CEF no arquivo. **Desconhecido:** se e como são chamados, a ordem efetiva, processo auxiliar e sequência completa de arranque, pois não houve análise de fluxo nem execução. |
| Navegação e domínios funcionais | Strings incluem modelos de rota `open.spotify.com` para pesquisa, artista, faixa, playlist e biblioteca, além de `content-feed`, `dailymix`, `local` e `audiofile`. | **Observado:** esses nomes estão embutidos no executável. **Inferência limitada:** correspondem a conceitos de navegação/conteúdo reconhecidos pelo cliente. Strings isoladas não demonstram que cada tela esteja disponível ou ativa nesta versão. |
| Player e estado | O binário contém termos de conteúdo musical e rotas de faixa/áudio. | **Desconhecido:** arquitetura do player, fila, estados de reprodução, tratamento de falhas e separação entre UI e serviços não podem ser determinados a partir destas strings. Não se tentou reconstruir protocolo ou API privada. |
| Persistência e configuração | A string `User Data` ocorre no arquivo. | **Observado:** existe esse literal. **Desconhecido:** local, formato e semântica do armazenamento da aplicação; o literal não prova quais preferências ou dados são persistidos. |
| Acessibilidade | O arquivo contém `accessibility_narration` e `accessibility_narration/intro`; GTK/ATK também constam como dependências. | **Observado:** há nomes relacionados a narração/acessibilidade e uma dependência de infraestrutura ATK. **Desconhecido:** controles, cobertura e comportamento acessível efetivamente expostos. |
| Mitigações / carregamento | `GNU_RELRO`, `GNU_STACK` RW e flags `NOW PIE` aparecem nos cabeçalhos dinâmicos/program headers; RUNPATH é `$ORIGIN`. Um `LOAD` aparece com permissões RWE. | **Observado:** essas marcações constam no ELF. A segmentação RWE merece cautela na leitura de segurança; não foi investigada nem atribuída a uma causa. Não é necessário para orientar o MVP. |

## Aplicação independente no Auralume

- Manter a arquitetura em camadas: UI PySide6, player, biblioteca e persistência SQLite como componentes próprios; a inspeção não justifica adotar CEF nem GTK.
- Tratar navegação, reprodução, fila, carregamento e erros como estados explícitos do Auralume, com testes dos serviços sem depender da janela. Isso é uma recomendação de desenho, não uma descrição comprovada do Spotify.
- Expor nomes acessíveis e estados de controle no Qt desde o início; a evidência de termos ATK/narração apenas reforça considerar acessibilidade, sem indicar implementação específica.
- Fornecer player e biblioteca locais funcionais sem rede. O binário inspecionado não permite concluir que qualquer serviço remoto ou endpoint seja livremente acessível ou apropriado para reutilização.

## Limitações e checklist

Respondido: identidade/arquitetura ELF, dependências diretas, tecnologias de UI prováveis, presença de termos de navegação e indícios textuais de acessibilidade. Parcial: inicialização (APIs CEF identificadas, ordem não observada). Não resolvido: módulos internos, organização visual real, player e seu gerenciamento de estado, persistência, configurações, acessibilidade em execução e tratamento de erros.

A investigação permanece deliberadamente limitada a metadados, dependências e strings do executável. O provedor REA indisponível impede gerar seu layout canônico; a análise alternativa basta para orientar decisões gerais de arquitetura e não bloqueia o desenvolvimento do Auralume.
