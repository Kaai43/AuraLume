# Qt/PySide: inventário de avisos de terceiros do bundle

Versão observada: PySide6 / Qt 6.12.0. Auditoria estática do onedir Auralume em Ubuntu 26.04.1 amd64, 14/10/2026. Consulte [Licenses Used in Qt for Python](https://doc.qt.io/qtforpython-6/licenses.html) para avisos associados a PySide/shiboken e [Third-Party Code Used in Qt 6.12.0](https://doc.qt.io/qt-6/licenses-used-in-qt.html) para textos de licenças, atribuições e detalhes de componentes de terceiros. A página Qt informa que só devem ser reconhecidos os componentes de terceiros efetivamente distribuídos com a aplicação.

## Componentes presentes observados

O bundle contém bindings para **Qt Core, Qt D-Bus, Qt GUI, Qt Network e Qt Widgets**. Foram encontrados binários Qt dos módulos **Core, D-Bus, EglFS, GUI, Network, OpenGL, PDF, QML, Quick, SVG, Virtual Keyboard, Wayland Client, Widgets e XcbQpa**, junto a ICU 73. Plugins de plataforma, integração, imagem, tema, TLS e input context também estão presentes; o inventário e as quantidades estão em `docs/dependencies.md`.

Os módulos Qt 6.12 relacionados na página oficial incluem componentes de terceiros sob licenças permissivas e outras licenças. Para facilitar a revisão dos módulos observados neste bundle, a página oficial lista, entre outros:

| Módulo Qt observado | Componentes de terceiros enumerados pela documentação do Qt 6.12 (licenças na página oficial) |
|---|---|
| Core | zlib, PCRE2, double-conversion, TinyCBOR, BLAKE2, algoritmos de hash e dados Unicode/CLDR |
| D-Bus | Headers de libdbus |
| GUI | FreeType, HarfBuzz, libjpeg-turbo, libpng, pixman, MD4C, perfis/fontes e componentes gráficos |
| Image Formats / plugins | libtiff e libwebp |
| Network | Public Suffix List e libpsl |
| PDF (`libQt6Pdf.so.6`, `libqpdf.so`) | PDFium/Chromium, FreeType, Abseil, ICU, fast_float, libjpeg-turbo, libpng e zlib |
| QML | JavaScriptCore Macro Assembler |
| Quick | Yoga |
| Virtual Keyboard | OpenWnn, PinyinIME e Traditional Chinese IME |

A lista acima identifica componentes anunciados pelo Qt para esses módulos, não afirma que cada arquivo de terceiros esteja incorporado em cada binário do bundle. Confira os textos completos, versões e licenças de cada item nas páginas oficiais. O Qt 6.8+ também publica SBOMs SPDX; use o SBOM da distribuição/build exata quando disponível. Não use as listas de Qt WebEngine ou Qt Multimedia: esses módulos não foram encontrados neste bundle.

## Licenças de PySide e shiboken

Os metadados observados de PySide6, Essentials, Addons e shiboken6 declaram a escolha entre LGPL-3.0-only, GPL-2.0-only ou GPL-3.0-only. Os textos GPLv2, LGPLv3 e GPLv3 disponibilizados em `packaging/licenses/` cobrem os textos dessas opções; o projeto identifica sua licença em `LICENSE`. A existência dos textos, sozinha, não satisfaz requisitos de relinkabilidade, código-fonte correspondente ou demais condições de uma opção LGPL/GPL. Revise o modo de distribuição escolhido antes de publicar.

## Conteúdo omitido e revisão de escopo

O pacote atual não contém libmpv nem FFmpeg. `libmpv2` é dependência externa do sistema e seu aviso Ubuntu separado não substitui os avisos Qt.

O conteúdo atual ainda inclui QtPdf/PDF imageformat, Qt QML/Quick e Qt Virtual Keyboard apesar de não haver uso correspondente na interface do Auralume. Sua remoção é uma otimização pendente: após alterar a coleta, repita a varredura de binários e a validação dos plugins/backends suportados; remova ou mantenha as entradas desta lista de acordo com o bundle efetivamente entregue. A relação de bibliotecas/plugins Qt pode mudar após poda ou rebuild.
