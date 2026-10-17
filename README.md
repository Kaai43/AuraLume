# Auralume

**Your Music, Your Way** — player desktop gratuito e sem login, com dados locais.

## Iniciar

Build Ubuntu x86-64: abra `dist/Auralume/Auralume`, execute `./run.sh` ou, dentro da pasta extraída, `./Auralume`.
Mantenha a pasta `_internal` ao lado do executável. O pacote é PyInstaller **onedir**, não AppImage.

Requisitos do sistema: Ubuntu 26.04 x86-64, sessão gráfica, `libmpv2`, bibliotecas Qt/X11/Wayland e saída de áudio do sistema. Neste host estão instalados `libxcb-cursor0`, `libxkbcommon-x11-0`, `libegl1` e `libgl1`. O build desta sessão não foi validado em Ubuntu 22.04/24.04; para essas versões gere o build em ambiente compatível. Não é necessário Python no destino do executável.

Para registrar no menu de aplicativos, execute explicitamente `dist/Auralume/install-desktop.sh` após escolher uma localização permanente para a pasta. Isso cria um atalho no perfil local; não precisa sudo.

## Usar

- **Importar arquivos/pasta:** varre áudio local e lê título, artista, álbum, gênero e duração quando disponíveis. MP3, FLAC, OGG, Opus, WAV, M4A e outros formatos reconhecidos por Mutagen. `cover.jpg/png` e `folder.jpg/png` ao lado do arquivo aparecem como capa.
- **Pesquisar:** título, artista, álbum e gênero, incluindo busca sem acentos.
- **Ouvir:** duplo clique em uma música ou clique num cartão. Player com pausa, próxima/anterior, posição, volume, aleatório, repetição e fila. Botão direito adiciona músicas à fila, favoritos ou playlists.
- **Playlists:** crie uma lista, adicione pelo menu de uma faixa e abra por duplo clique. O menu permite remover faixas e excluir a lista sem apagar arquivos de áudio.
- **Para Você:** preferências em Configurações (ex.: `jazz, piano`), favoritos, histórico, playlists e metadados alimentam um ranking local com diversidade de artistas. Não existe catálogo remoto próprio; importe suas músicas para começar.
- **Origem autorizada:** cole uma URL pública e confirme sua autorização. yt-dlp resolve uma faixa individual em segundo plano; áudio é transmitido por libmpv sem download permanente. Não há cookies, credenciais, DRM ou acesso a conteúdo privado. Quando não houver reprodução disponível, use a ação de abrir a origem no navegador.
- **Atalhos:** Ctrl+O para importar; Ctrl+F para pesquisar; Espaço para pausar/reproduzir fora de campos de texto.

Dados: `${XDG_DATA_HOME:-~/.local/share}/Auralume/library.sqlite3`; diagnóstico local em `auralume.log`. `--data-dir PASTA` escolhe outro diretório. Não há servidor do Auralume nem envio do histórico. Ao abrir uma origem, o provedor da URL recebe a conexão de rede.

## Desenvolver e verificar

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
.venv/bin/python -m auralume
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest -q
./scripts/build.sh
dist/Auralume/Auralume --diagnostics
dist/Auralume/Auralume --smoke-test
```

O teste HTTP usa apenas loopback e WAV gerado pelo próprio teste. Em sandbox, pode ser necessária permissão para criar esse socket. Os testes de áudio usam saída `null`, sem som físico. Para verificar um arquivo no executável: `Auralume --smoke-test --play /caminho/faixa.wav`; `--screenshot captura.png` salva a janela renderizada. `--diagnostics` não cria banco nem exige sessão gráfica.

`--authorized-source URL` abre uma origem cuja reprodução você autoriza explicitamente. `scripts/verify_release.py` testa o ELF numa cópia temporária em outro diretório, decodificando WAV, MP3, FLAC e áudio por HTTP local, sem usar o Python de desenvolvimento dentro do executável. FFmpeg é necessário apenas para gerar os arquivos desse verificador, não para iniciar o Auralume.

## Arquitetura e continuidade

`auralume/ui/` contém widgets; `controller.py` conecta sinais; SQLite em `database.py`; `library.py` lê metadados; `queue.py` define ordem; `player.py` adapta libmpv; `sources.py` encapsula yt-dlp; `recommendations.py` usa sinais locais; `workers.py` entrega resultados ao thread Qt sem bloquear a janela.

Evidências e próximos passos: [progresso](docs/progress.md), [próxima tarefa](docs/next-task.md), [investigação REA](docs/reverse-engineering.md), [dependências](docs/dependencies.md), [integração HTTP](docs/source-integration.md).

## Licenças

Código original do Auralume: GPL-3.0-or-later, texto em `LICENSE`. Dependências mantêm suas licenças; veja `packaging/licenses/` no código-fonte ou `_internal/licenses/` no executável. A opção onedir mantém bibliotecas Qt substituíveis. O código-fonte acompanha o projeto e o arquivo `Auralume-0.1.0-source.tar.gz`; nenhuma publicação é feita automaticamente. Conteúdo musical não está incluído e continua sujeito à autorização de sua origem.

Referências de implementação: [API Python do yt-dlp](https://github.com/yt-dlp/yt-dlp#embedding-yt-dlp), [manual mpv](https://mpv.io/manual/stable/), [Qt for Python](https://doc.qt.io/qtforpython-6/), [PyInstaller](https://pyinstaller.org/en/stable/usage.html). Design e código do Auralume são independentes; nenhum recurso proprietário do Spotify foi reutilizado.

## Windows x64 — preparação em andamento

O porte possui carregamento privado de DLLs, diagnósticos e um pipeline manual de build/testes. **Ainda não há pacote Windows validado nesta sessão.** Instruções, dependências fixadas e limitações: [docs/windows-build.md](docs/windows-build.md). Nenhuma release é publicada automaticamente; revisão de licenças e aprovação do responsável são necessárias antes de distribuir binários.
