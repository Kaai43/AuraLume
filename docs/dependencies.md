# Dependências, licenças e requisitos de distribuição

Inventário do ambiente em 2026-10-14, para a configuração declarada em `pyproject.toml`. Versões são observadas no `.venv` e no host; não representam versões mínimas de todas as instalações Ubuntu.

## Ambiente verificado

- Host: Ubuntu 26.04.1 LTS, amd64, glibc 2.43.
- Python do `.venv`: 3.14.4. Python do sistema: 3.14.3.
- PySide6, PySide6-Essentials, PySide6-Addons e shiboken6: 6.12.0; Qt runtime: 6.12.0.
- `mpv` Python package: 1.0.8. O nome da distribuição é `mpv`; ela fornece o binding Python chamado `mpv` (o metadado não usa o nome `python-mpv`).
- `mutagen`: 1.48.1. `yt-dlp`: 2026.8.19. PyInstaller: 6.22.3.
- `pytest` 9.1.1 e setuptools 84.0.0 estão instalados para desenvolvimento/testes/build; não são dependências runtime declaradas pela aplicação.
- `libmpv.so.2` está disponível no sistema pelo pacote Ubuntu `libmpv2` 0.41.0-2ubuntu4. O binário `mpv` da mesma versão também existe no host, mas o binding Python carrega a biblioteca compartilhada; a aplicação não precisa executar o CLI `mpv`.
- A licença escolhida para o Auralume é GPL-3.0-or-later; o texto GPLv3 está anexado em `packaging/licenses/GPL-3.0.txt`.

## Dependências observadas

| Componente | Versão observada | Licença publicada nos metadados/documentação | Uso e distribuição |
|---|---:|---|---|
| Python | 3.14.4 no `.venv`; 3.14.3 sistema | PSF License 2.0 | PyInstaller usa o runtime da versão do build. O alvo não precisa ter Python instalado para executar o onedir gerado, mas precisa das bibliotecas de sistema. Aviso PSF copiado. |
| PySide6 + Essentials + Addons | 6.12.0 | `LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only` | O bundle contém wrappers de QtCore, QtDBus, QtGui, QtNetwork e QtWidgets, além de bibliotecas e plugins descritos na auditoria abaixo. Foram incluídos textos LGPLv3 e GPLv2/v3 e um inventário dos componentes Qt de terceiros. |
| shiboken6 | 6.12.0 | `LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only` | Runtime/bindings usado pelo PySide6 e incluído no bundle; não confundir com `shiboken6-generator`, que não faz parte deste inventário. |
| `mpv` (binding Python) | 1.0.8 | GPLv2+ ou LGPLv2.1+ | Binding carrega `libmpv` via biblioteca compartilhada. Os dois textos de licença fornecidos pela distribuição Python foram copiados. |
| libmpv (`libmpv.so.2`) | 0.41.0-2ubuntu4 | Registro Debian/Ubuntu do pacote fonte `mpv`; ver observação abaixo | Dependência do sistema, fora do onedir PyInstaller. Requer `libmpv2` e as bibliotecas/runtime de áudio e codecs fornecidas pelo Ubuntu. Não foi copiada a biblioteca binária. |
| mutagen | 1.48.1 | `GPL-2.0-or-later` | Dependência Python direta para metadados; o texto `COPYING` foi copiado. O projeto escolheu GPL-3.0-or-later para o Auralume; verifique o cumprimento das obrigações aplicáveis ao conjunto distribuído. |
| yt-dlp | 2026.8.19 | Unlicense | Dependência Python direta; texto `LICENSE` foi copiado. Licenças e termos das origens de mídia continuam aplicáveis separadamente. |
| PyInstaller | 6.22.3 | GPL-2.0-or-later com exceção do bootloader; partes de runtime têm avisos próprios | Ferramenta de build. O pacote fornece `COPYING.txt`, copiado. A exceção cobre combinação/distribuição do bootloader conforme o aviso upstream; ela não elimina outras obrigações de dependências incluídas. |
| pytest / setuptools | 9.1.1 / 84.0.0 | MIT / MIT | Ferramentas de desenvolvimento e build; não entram no runtime da aplicação por declaração atual. |

## Bibliotecas do sistema e formato onedir

PyInstaller não inclui `glibc` nem bibliotecas que espera que existam no sistema (`/lib` e `/usr/lib`). Portanto `dist/Auralume/` não é um AppImage nem um pacote autocontido. O binding `mpv` procura `libmpv.so.2`; o host verificado tem `libmpv2` instalado. Bibliotecas transitivas de libmpv, servidor gráfico, plugins Qt, fontes e áudio podem depender do conjunto de pacotes do sistema e devem ser verificadas no build final.

### Auditoria do primeiro bundle (14/10/2026, substituído)

O primeiro onedir foi auditado e **não é o artefato candidato à entrega**: continha `_internal/libmpv.so.2` e bibliotecas FFmpeg/codec sob `_internal`, coletadas pela análise de `ctypes` do binding `mpv`. O executável principal era ELF64 x86-64; `ldd` não indicou dependências diretas ausentes no host, mas esse resultado não valida todas as bibliotecas incluídas nem portabilidade. O coordenador ajustou o spec para excluir bibliotecas do sistema; o bundle atualizado confirmou a remoção, conforme a auditoria abaixo.

Na análise estática de `build/Auralume/Analysis-00.toc`, os imports da aplicação incluíam somente `PySide6.QtCore`, `PySide6.QtGui` e `PySide6.QtWidgets`; ainda assim, o primeiro bundle carregava wrappers e plugins Qt adicionais. A revisão abaixo cobre o onedir reconstruído.

### Auditoria do bundle atual (14/10/2026)

O onedir tem 155 MB e 321 arquivos. O executável principal é ELF64 x86-64, dinamicamente ligado. `readelf -d` mostra como requisitos diretos do bootloader `libdl.so.2`, `libz.so.1`, `libpthread.so.0` e `libc.so.6`. Uma varredura com `ldd` dos 184 arquivos ELF candidatos (`Auralume` e objetos com `.so`) não encontrou `not found` no host Ubuntu 26.04.1. Não é prova de compatibilidade com outros releases.

**Resultado importante:** não há `libmpv.so`, `libavcodec`, `libavformat`, `libavfilter`, `libswresample`, `libswscale` ou binário FFmpeg no bundle. O pacote de licenças de Ubuntu `libmpv2` está presente somente como informação de dependência. Portanto, `libmpv2` é uma dependência externa necessária para reprodução e deve ser instalada pelo usuário no Ubuntu. Os codecs/bibliotecas disponíveis serão os oferecidos pelo `libmpv2` e pelo sistema instalado; o Auralume não empacota FFmpeg.

Os wrappers Qt encontrados são `QtCore`, `QtDBus`, `QtGui`, `QtNetwork` e `QtWidgets`. O diretório de bibliotecas Qt também inclui Core, DBus, EglFS, Gui, Network, OpenGL, Pdf, Qml, Quick, Svg, VirtualKeyboard, WaylandClient, Widgets e XcbQpa, além de ICU 73. Plugins presentes: `egldeviceintegrations` (3), `generic` (5), `iconengines` (1), `imageformats` (10), `networkinformation` (3), `platforminputcontexts` (3), `platforms` (9), `platformthemes` (2), `tls` (2), `wayland-decoration-client` (2), `wayland-graphics-integration-client` (5), `wayland-shell-integration` (5) e `xcbglintegrations` (2). O bundle inclui mais módulos e plugins do que os usados diretamente pelo código da aplicação; a página oficial e o inventário de módulos estão em [`../packaging/licenses/Qt-6.12.0-third-party-notices.md`](../packaging/licenses/Qt-6.12.0-third-party-notices.md).

O excesso identificável inclui o plugin PDF de formatos de imagem (`plugins/imageformats/libqpdf.so`) e as bibliotecas QtPdf (4.4 MB); se o Auralume não abre PDFs via imagem, excluir esse plugin na coleta deve retirar a dependência. `plugins/platforminputcontexts/libqtvirtualkeyboardplugin.so` não é necessário para um teclado virtual embutido; ele puxa QtVirtualKeyboard e QtVirtualKeyboardQml e, por consequência, bibliotecas Qml/Quick/OpenGL. Excluí-lo da coleta é candidato a reduzir o bundle. O pacote também contém Qt Qml/Quick e plugins de plataformas alternativas (EGLFS, LinuxFB, VNC, Vulkan, etc.) enquanto o objetivo atual é desktop Ubuntu X11/Wayland. Podar deve ser feito no spec e seguido por smoke tests de inicialização, Qt platform plugin e renderização nos backends mantidos; nenhuma poda foi aplicada nesta auditoria.

`ldd` de todos os objetos incluídos resolveu dependências no host, mas revelou dependências transitivas externas do ambiente gráfico. A lista observada inclui X11/XCB, `libxcb-cursor`, `libxkbcommon-x11`, EGL/GL, Wayland, GTK3 (plugin de tema), fontconfig/FreeType, DBus, OpenSSL (plugin TLS), zlib e bibliotecas padrão do sistema. A resolução por `ldd` reflete também plugins alternativos empacotados e não determina por si só quais pacotes Ubuntu são necessários em todos os caminhos de execução. No host, `libxcb-cursor0`, `libxkbcommon-x11-0`, `libegl1` e `libgl1` estão instalados; validar o pacote mínimo no destino.

No Ubuntu amd64, instalar `libmpv2` do repositório da própria versão é o requisito explícito conhecido. Recomenda-se confirmar dependências reais do executável/bibliotecas congelados com `readelf` (não assumir que a lista deste host se aplica a todas as versões Ubuntu). A disponibilidade de hardware, backend de áudio ou codec pode variar conforme o sistema.

## Alvos Ubuntu e compatibilidade

O ambiente desta sessão é **Ubuntu 26.04.1 LTS amd64**; é o único alvo Ubuntu verificado para este inventário. Ubuntu 22.04 LTS e 24.04 LTS estão **não testados** nesta sessão. Um executável PyInstaller não deve ser presumido compatível com versões anteriores: no Linux, `glibc` não é empacotada e o programa pode exigir símbolos de uma glibc mais recente que a instalada no usuário. A documentação do PyInstaller recomenda construir no Ubuntu mais antigo que se pretende suportar e testar cada alvo. Para prometer suporte simultâneo a 22.04, 24.04 e 26.04, produza e teste o build em 22.04 (ou mantenha builds separados) e valide também o onedir em cada release.

Em consequência, um build produzido neste host Ubuntu 26.04.1 **não pode ser anunciado como compatível com Ubuntu 22.04 ou 24.04 sem testes**. A versão do Ubuntu e a lista de dependências não substituem testes de inicialização, reprodução, áudio e plugins Qt.

## Avisos e auditoria antes de distribuir

Os textos copiados estão em [`../packaging/licenses/`](../packaging/licenses/README.md). PySide6/Qt não incluiu arquivos de licença nos metadados locais dos wheels; foram anexados textos LGPLv3 e GPLv2/v3 do sistema. Qt publica os componentes de terceiros por módulo e SBOMs SPDX do Qt 6.8 em diante. O inventário em `packaging/licenses/Qt-6.12.0-third-party-notices.md` identifica os módulos observados e aponta para os avisos completos oficiais. Refaça o cruzamento sempre que o conjunto de Qt libraries/plugins mudar e inclua os avisos aplicáveis no artefato final.

Os metadados de mutagen declaram GPL-2.0-or-later e a distribuição PySide6 oferece LGPLv3/GPLv2/GPLv3. O Auralume adotou GPL-3.0-or-later; os avisos anexos não constituem parecer jurídico nem provam que todas as obrigações de código-fonte/relinking aplicáveis ao pacote concreto foram satisfeitas.

O pacote Ubuntu `libmpv2` usado no host foi compilado pelo ecossistema Ubuntu. O arquivo de copyright desse pacote observa que os binários do pacote-fonte mpv são GPL-3+ quando ligados a libsmbclient; essa observação não foi extrapolada como conclusão sobre a licença de cada objeto compartilhado ou sobre outros builds. O arquivo local foi guardado para referência, mas libmpv não é copiada para o bundle.

## Referências oficiais

Avisos das dependências Python transitivas coletadas pelo hook yt-dlp estão em `packaging/licenses/python-dependencies/`: requests 2.34.2, urllib3 2.8.0, certifi 2026.7.22, idna 3.20, charset-normalizer 3.5.2, websockets 17.2, brotli 1.2.0, pycryptodomex 3.24.1, yt-dlp-ejs 0.8.0, setuptools 84.0.0 (incluindo avisos vendorizados) e packaging 26.3. `manifest.json` registra versões e SHA-256; `scripts/collect_licenses.py` compara cada cópia com o arquivo instalado.

- [Licenciamento do Qt](https://doc.qt.io/qt-6/licensing.html) e [licenças de terceiros do Qt 6.12](https://doc.qt.io/qt-6/licenses-used-in-qt.html).
- [Qt for Python: licença e componentes de terceiros](https://doc.qt.io/qtforpython-6/licenses.html), [detalhes dos wheels](https://doc.qt.io/qtforpython-6/package_details.html) e [uso com PyInstaller](https://doc.qt.io/qtforpython-6/deployment/deployment-pyinstaller.html).
- [PyInstaller: operação e bibliotecas não empacotadas](https://pyinstaller.org/en/stable/operating-mode.html), [compatibilidade Linux/glibc](https://pyinstaller.org/en/stable/usage.html#making-gnu-linux-apps-forward-compatible) e [licença](https://pyinstaller.org/en/stable/license.html).
- [Ubuntu: ciclo de suporte](https://ubuntu.com/about/release-cycle).
- [mpv: arquivo de direitos autorais/licenças](https://github.com/mpv-player/mpv/blob/master/Copyright).
