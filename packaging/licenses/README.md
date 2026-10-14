# Avisos de terceiros

Os arquivos desta pasta foram copiados de textos presentes no ambiente de desenvolvimento em 2026-10-14. Seus nomes registram a origem e versão conhecida quando aplicável.

- `LGPL-3.0.txt`: texto LGPLv3 disponível em `/usr/share/common-licenses`; referência de licença para a opção LGPL da pilha Qt/PySide.
- `GPL-3.0.txt`: texto GPLv3 disponível em `/usr/share/common-licenses`; licença escolhida pelo projeto para o Auralume.
- `GPL-2.0.txt` e `LGPL-2.1.txt`: textos de licença encontrados no ambiente para as opções licenciadas do binding Python `mpv`.
- `python-mpv-1.0.8-GPL.txt` e `python-mpv-1.0.8-LGPL.txt`: arquivos de licença fornecidos pelo pacote Python `mpv` 1.0.8.
- `mutagen-1.48.1-COPYING.txt`, `yt-dlp-2026.8.19-LICENSE.txt`, `PyInstaller-6.22.3-COPYING.txt`: arquivos fornecidos pelos pacotes Python instalados.
- `Python-3.14-copyright.txt`: arquivo de copyright/licenças instalado pelo pacote Ubuntu Python 3.14.
- `Ubuntu-libmpv2-0.41.0-2ubuntu4-copyright.txt`: arquivo Debian copyright instalado para o pacote Ubuntu que fornece a dependência externa `libmpv.so.2`; o arquivo é informativo e não inclui a biblioteca.
- `Qt-6.12.0-third-party-notices.md`: inventário dos módulos Qt/PySide observados no onedir e referência aos avisos oficiais de terceiros por módulo. Ele não substitui a checagem dos componentes efetivamente presentes após cada rebuild.

Esta pasta é material de origem para o pacote, não uma afirmação de que todos os avisos necessários já estejam incorporados em `dist/Auralume/`. O bundle auditado está documentado em `docs/dependencies.md`; o bundle atual não inclui ainda o novo inventário Qt deste diretório. Inclua este inventário e os textos/atribuições aplicáveis no próximo artefato e revise-os após qualquer mudança dos módulos/plugins distribuídos.
