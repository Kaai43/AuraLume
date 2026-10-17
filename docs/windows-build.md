# Distribuição Windows x64 — registro de execução

## Missão atual

Windows é o único trabalho ativo, por instrução explícita do usuário. Temas/mobile já presentes são preservados, sem desenvolvimento adicional. O workflow multiagente removido não será recriado. Execução por um único agente. Em 17/10/2026, o usuário autorizou o push dos fontes atuais para validar manualmente o porte, excluindo AGENTS.md, Registros e pacotes TAR/AppImage. Tags e releases continuam sem autorização. As referências abaixo à ausência de push e ao registro ainda vazio descrevem o estado anterior a essa autorização.

## Inventário inicial

- Branch `main`, HEAD `9d9676680fce52f1083e28df8d959279d84d936c`. Alterações anteriores em app/UI/temas/docs e projeto mobile não rastreado; remoção intencional de `AURALUME_WORKFLOW.md` preservada.
- `origin/main` consultado anteriormente: `e8f81470b5e2e8907ad7e4adc96ff648fc67bc44` (apenas README diferente); não feito merge nem push.
- Python 3.14.4/Qt 6.12/libmpv Linux locais. Não há Windows/Wine/PowerShell local. Existe CLI `gh` com consultas de leitura funcionais.
- `run.py` é o entry point válido. Spec atual onedir exclui bibliotecas do sistema no Linux. Workflow Windows manual existe, mas não obtém libmpv.

## Causa histórica verificada

GitHub API do [job 116065405539](https://github.com/Kaai43/AuraLume/actions/runs/38626057817/job/116065405539) confirma falha em testes, antes do build. Log obtido por `gh api --method GET repos/Kaai43/AuraLume/actions/jobs/116065405539/logs`: **6 failed, 52 passed in 24.57s**, diagnóstico libmpv `None`, player com `OSError`. Log local de investigação: `/tmp/auralume-windows-historical.log`.

O binding instalado `mpv` 1.0.8 busca mpv-2.dll/libmpv-2.dll no PATH ou ao lado de mpv.py durante o import e carrega via ctypes. `os.add_dll_directory` sozinho não resolve a descoberta feita por esse binding. O pipeline histórico instala somente pacotes Python. Esses fatos confirmam a lacuna de fornecimento/descoberta; outras falhas de portabilidade ainda dependem de testes no runner.

## Plano de execução

1. Testes e implementação centralizada da descoberta/carregamento DLL, diagnóstico real e caminhos de dados.
2. Fixar pacote nativo x64 por URL/digest; inspecionar PE/imports/licenças e automatizar staging.
3. Adaptar spec e pipeline manual: diagnóstico, suíte inteira, onedir, áudio próprio, ZIP extraído fora do build, manifesto e artifact de revisão.
4. Regressão Linux e build local isolado, sem sobrescrever publicação existente.
5. Solicitar autorização específica para enviar código e disparar Windows somente após entregar diff e verificações locais. Não confundir preparação com Windows validado.

## Seleção nativa em investigação

O site [mpv Installation](https://mpv.io/installation/) aponta builds comunitários shinchiro e MSYS2; não são binários oficiais de release do mpv. Selecionado para auditoria: shinchiro `20261015`, `mpv-dev-x86_64-20261015-git-492bae0768.7z` (x86_64 baseline, não v3).

SHA-256 publicado via API GitHub e conferido no download local:
`5db58c1768587b35f2d8daa11b53de4aec58197c00ea1d676f998f183a358ba8`.

MSYS2 é alternativa mantida, mas distribui dependências como pacotes separados; um staging deve resolver recursivamente todo o conjunto. Usar mpv.exe isolado não satisfaz o binding. A opção comunitária com DLL permite inspeção de um pacote fixo; aceitação de runtime/licenças ainda pendente nesta etapa.

## Estado

Preparação em andamento. **Auralume.exe e ZIP Windows ainda não gerados nem validados.** Áudio físico Windows 10/11 não testado. Resultados serão acrescentados aqui após execução.

### Continuidade de 17/10/2026

Os manifestos das três Actions fixadas foram consultados por API: todos declaram `using: node24`. O aviso Node20 do job histórico não era a etapa fatal: checkout/Python terminaram com sucesso; os testes registraram 52 aprovados e 6 falhas de libmpv. Referência: [comunicado GitHub](https://github.blog/changelog/2025-09-19-deprecation-of-node-20-on-github-actions-runners/).

Corrigido o verificador Windows para fechar conexões SQLite explicitamente antes de limpar a pasta temporária. O context manager da conexão apenas confirma/reverte transações; não fecha o handle. Teste de regressão reproduzido antes da implementação, aprovado depois.

Regressão atual: **124 passed**, 0 falhas, 0 ignorados, em 8,41 s; XML em `docs/evidence/windows/pytest-linux.xml`. A primeira tentativa restrita encontrou 122 passes/1 erro de permissão de socket no teste HTTP; execução com loopback permitido passou integralmente. Cópia isolada do código Windows baseada em `origin/main` e sem temas/mobile: **75 passed** em 6,65 s, XML `pytest-windows-source-linux.xml`.

Patch revisável: `dist/windows-review/windows-port.patch`, validado com `git apply --reverse --check` contra sua cópia de fontes. Preserva a exclusão intencional do workflow multiagente e o README remoto; a árvore principal e os trabalhos independentes continuam no lugar. Ainda não houve commit/push/disparo de workflow. `Registros/` foi criada **vazia**; o arquivo `17-10-2026.txt` só será escrito depois de concluir o porte, conforme pedido.

PyInstaller Linux recompilado em `dist/windows-port-linux-check/Auralume/Auralume`; execução relocada com `frozen=true` e engine real aprovado em WAV, MP3, FLAC e HTTP local, sempre `ao=null`. Relatório: `docs/evidence/windows/linux-port-acceptance.json`; captura: `linux-port-smoke.png`. Warnings do build: módulos opcionais `urllib3.contrib.emscripten` (sem `js`) e `curl_cffi` ausente; as verificações mencionadas passaram. Áudio audível não testado. HEAD remoto consultado novamente: `e8f81470b5e2e8907ad7e4adc96ff648fc67bc44`, sem alteração desde a base do patch.

## Implementação atual

- `auralume/native.py`: valida PE AMD64; resolve `vendor/mpv` no source ou `_internal/native` no frozen; conserva handles `add_dll_directory`; PATH temporário somente durante import do binding, restaurado em `finally`. O frozen ignora overrides externos. Não depende do cwd. Não foi necessário duplicar isso em runtime hook: ambos os consumidores usam o módulo antes do import mpv, incluído explicitamente em hiddenimports.
- Diagnóstico cria/encerra engine real `ao=null`, registra DLL carregada, erro e versão. No Windows consulta o caminho do Vulkan já carregado pelo sistema operacional. Saída CLI JSON usa escapes ASCII para funcionar também em consoles com codificação restrita. Falha retorna código 1, sem Qt/DB.
- `auralume/paths.py`: Windows usa LOCALAPPDATA/Auralume. Se há somente biblioteca no caminho legado XDG/.local/share, mantém seus dados no lugar; não migra/apaga. Linux XDG e `--data-dir` preservados.
- Spec compartilhado: onedir, entry point `run.py`, SVG em `_internal/packaging`, metadados e avisos; somente Linux exclui bibliotecas do sistema. Windows inclui `libmpv-2.dll` e `vulkan-1.dll`. Console mantido para diagnósticos nesta primeira distribuição.
- `scripts/windows_native.py`: download por URL/commit fixado, hash antes de extrair, somente DLL esperada da 7z; fontes tar com filtro de extração seguro. PE imports são comparados com DLLs do sistema e dependências distribuídas. Vulkan Loader é compilado nativamente no runner. FFmpeg EXE serve apenas aos testes e fica fora do ZIP.
- `scripts/verify_windows.py`: inventário de arquivos/hash/tamanho, rejeição de arquivos privados óbvios, ZIP e reextração em caminho Unicode com espaços, cwd externo, PATH reduzido e isolamento de variáveis Python/Qt. Diagnósticos exigem `frozen=true`, libmpv e Vulkan vindos do pacote; remove temporariamente libmpv no diretório temporário para comprovar falha sem fallback externo. Reprodução WAV/MP3/FLAC própria, captura Qt, persistência de registros previamente gravados em SQLite entre execuções; criação por UI é coberta pela suíte do controlador.

## Resultado da auditoria nativa

**VERIFICADO estaticamente no Linux**, sem executar DLL Windows:

- Arquivo .7z: 31.559.237 bytes, SHA-256 acima.
- `libmpv-2.dll`: 121.001.472 bytes; SHA-256 `154a1610c266563e131c328349af396dd9af693eeb049d0c04ef196324541539`.
- PE AMD64 (`0x8664`), 206 exports, incluindo `mpv_client_api_version`.
- Imports incluem **vulkan-1.dll de carga obrigatória**, não delay-load; o ZIP dev não fornece essa DLL. As demais importações observadas são Windows/API sets. Isto é evidência de uma dependência transitiva, não de seu carregamento bem-sucedido.
- Escolhido Vulkan Loader/Headers **1.4.328**, commits e SHA-256 dos tarballs oficiais medidos e registrados em `packaging/windows/native-lock.json`. Compilação com Visual Studio x64 segue as opções da versão consultada, sem baixar dependências móveis via UPDATE_DEPS. **Compilação Windows ainda não executada.**
- FFmpeg de teste também importa Vulkan; o staging coloca a DLL compilada ao lado desse encoder, fora do pacote Auralume. SHA-256 do .7z do encoder conferido: `dc123b3ef138915c7c7b9fd1afaddce815c3163c496a5eaa63cf7945e7e475ab`.
- Todas as 30 versões de `requirements-windows.txt` resolveram wheels compatíveis com CPython 3.12/Windows x64 em `pip --dry-run --ignore-installed --only-binary=:all: --platform win_amd64 --python-version 3.12`. Isso não equivale à instalação/execução em Windows.
- Extrator py7zr local não suportou BCJ2; substituído por 7-Zip do pacote Ubuntu extraído em `/tmp`, sem sudo/instalação global. O runner usa seu 7-Zip instalado. Ferramentas de auditoria não entram nas dependências runtime do aplicativo.

## Reprodução no Windows (a executar)

PowerShell, Python x64 3.12, Visual Studio 2022 com C++, CMake e 7-Zip no ambiente de build:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-windows.txt
python scripts/windows_native.py
$env:AURALUME_MPV_DIR = (Resolve-Path vendor/mpv).Path
python -m auralume --diagnostics
python -m pytest -q
python -m PyInstaller --noconfirm --clean Auralume.spec
python scripts/verify_windows.py --revision (git rev-parse HEAD) --ffmpeg .tools/windows-native/ffmpeg.exe
```

Verificar o código de saída de cada comando antes do seguinte. Workflow `.github/workflows/windows.yml` automatiza isso no `windows-2022`, com Actions oficiais fixadas por commit (tags v7 consultadas). Há apenas `workflow_dispatch`, permissões `contents: read`, nenhuma release automática, nenhum skip/xfail/continue-on-error em testes críticos.

O input `upload_candidate` é **false por padrão**. Habilitar só após revisão de licenças/fontes e autorização. Mesmo com upload desabilitado, o pipeline compila e valida o ZIP; os resultados ficam no job. Quando autorizado, o artifact conterá ZIP, SHA-256, inventário/relatório, capturas e JUnit. Retenção: 14 dias. Nada foi enviado/disparado nesta sessão.

## Licenças e limites de distribuição

**PUBLICAÇÃO BLOQUEADA.** O pacote dev shinchiro não traz licenças. A receita exata FFmpeg habilita GPL e version3; a DLL contém muitos componentes estáticos. Importações PE não fornecem um SBOM completo. `packaging/windows/README.md` e o Copyright mpv da revisão exata registram o que falta: textos/avisos de todos os componentes, revisões e fontes correspondentes, revisão dos plugins Qt coletados e forma de entrega de fontes. Links genéricos ou a GPL isolada não completam essa obrigação.

Vulkan tem avisos extraídos diretamente das fontes oficiais; Python e distribuições Python têm avisos coletados do ambiente real de build. A licença do Auralume não foi alterada. Builds e downloads permanecem ignorados em `.tools/`, `vendor/mpv/`, `build/` e `dist/`. Nenhuma mídia pessoal adicionada.

## Versionamento

A tag `v0.1.0` aponta para `15f54212fce64311a7cf3983e2513d225accfc3e`. Entre ela e origin/main existem apenas alterações de workflow/.gitignore/README; este porte, porém, altera código. Recomendação para o patch Windows isolado: **nova v0.1.1**, após aprovação e validação. Não anexar um código diferente como se fosse o build exato da tag antiga, nem mover a tag. v0.2.0 só deve ser reavaliada se o usuário decidir incluir funcionalidades independentes depois. Rascunho em `docs/windows-release-notes.md`.

## Fontes primárias consultadas

- [mpv: distribuições Windows](https://mpv.io/installation/)
- [python-mpv: carregamento e dependência nativa](https://github.com/jaseg/python-mpv)
- [Build shinchiro fixado](https://github.com/shinchiro/mpv-winbuild-cmake/releases/tag/20261015) e [job x64 de origem](https://github.com/shinchiro/mpv-winbuild-cmake/actions/runs/38657432408/job/116170448394)
- [Vulkan Loader: instruções de build](https://github.com/KhronosGroup/Vulkan-Loader/blob/v1.4.328/BUILD.md)
- [Python: add_dll_directory](https://docs.python.org/3/library/os.html#os.add_dll_directory)
- [PyInstaller: caminhos no frozen](https://pyinstaller.org/en/stable/runtime-information.html)
- [Actions checkout](https://github.com/actions/checkout), [setup-python](https://github.com/actions/setup-python), [upload-artifact](https://github.com/actions/upload-artifact)
- [Runner Windows 2022](https://github.com/actions/runner-images/blob/main/images/windows/Windows2022-Readme.md)
