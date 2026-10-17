# Arquitetura mobile do Auralume

Estado: proposta para a fundação Flutter do marco G2; ainda não é um app de distribuição.

## Ambiente local verificado (2026-10-15)

- SDK instalado somente em `.tools/flutter/` (ignorado pelo Git); cache de pacotes em `.tools/pub-cache/`; configuração/cache XDG em `.tools/`. As variáveis são passadas por comando, sem editar o ambiente global.
- Stable consultado no manifesto oficial `https://storage.googleapis.com/flutter_infra_release/releases/releases_linux.json`: Flutter **3.47.7**, Dart **3.13.5**, framework revision `abaf9c523780a608bd46686fd5e53740a07077f8`, release de 2026-10-08. Arquivo `flutter_linux_3.47.7-stable.tar.xz`; SHA-256 publicado e calculado no arquivo baixado: `af7455f540df951184c7953fbe3cf884766e7541dacf8571f9f582db03dd6230` (correspondência exata).
- `flutter --version --machine` e `dart --version`: passaram e confirmaram as versões acima. `flutter doctor -v`: executado; Flutter stable e rede foram reconhecidos. O host não tem Android SDK; também não tem Chrome, nem `clang++`, CMake, Ninja e `pkg-config` para builds Flutter desktop Linux. JDK não está instalado. Nenhum SDK Android/JDK foi instalado nesta preparação.
- Para o `doctor` acessar metadados e pub.dev, foi necessária execução com acesso de rede escalado após falha DNS dentro do sandbox. Todos os dados mutáveis ficam sob `.tools/`.
- Ainda não houve `flutter create`, `pub get` de um app, análise, testes Dart, build APK/iOS nem teste de áudio. A disponibilidade de Flutter/Dart não significa que esses artefatos foram validados.

## Limite e estrutura

O cliente desktop Python/PySide6 continua independente. O projeto Flutter será criado em `mobile/auralume_mobile/` pela CLI oficial (`flutter create --empty`) depois da liberação do G2. A UI usa Material 3 e adapta a navegação entre telas estreitas e largas. A implementação inicial não contém motor de áudio, importação funcional ou backend remoto; dados demonstrativos serão identificados como demonstração.

Estrutura inicial, sem camada extra de domínio até haver regras que a justifiquem:

```text
lib/
  app/                 # MaterialApp, navegação, composição de dependências
  core/                # erros, normalização e utilitários compartilhados
  features/
    library/            # catálogo e estado vazio
    player/             # controles visuais e contrato PlaybackService
    playlists/          # listas demonstrativas e contrato
    favorites/          # favoritos locais demonstrativos
    history/            # estado vazio/demonstrativo
    recommendations/    # Para Você, explicando o uso futuro da biblioteca local
    themes/             # parse do contrato de temas e tradução para ThemeData
  data/                 # implementações fake/local com status explícito
test/                   # modelos, fixtures, widgets e navegação
```

Seguir a separação recomendada pelo Flutter entre Views, ViewModels, Repositories e Services; não adicionar pacote de gerenciamento de estado sem necessidade. As telas da primeira fundação são Início, Biblioteca, Para Você, Favoritos, Playlists, Player e Configurações/Temas. Uma ação de reprodução informa que o motor ainda não está disponível. Não simular progresso, pausa ou áudio real.

## Contratos de domínio iniciais

- `Track`: `id`, `source`, `title`, `artist`, `album`, `duration`, `genre`, `artwork`, `isRemote`, `isFavorite`. Campos opcionais devem ser nulos ou ter defaults explícitos. Os metadados seguem o conceito do desktop, mas o objeto Dart não depende de classes Python/SQLite.
- `Playlist`: `id`, `name` e `trackIds` ordenados. `trackCount` é derivado da lista quando os itens estão carregados.
- `PlaybackState`: enum `unavailable`, `idle`, `loading`, `ready`, `playing`, `paused`, `failed`, mais faixa atual opcional, posição/duração e mensagem de erro segura. A implementação demo permanece `unavailable`.
- `ThemeDefinition`: `schemaVersion`, `id`, `name`, `author?` e mapa imutável dos 29 tokens de cor. O parser só aceita o contrato v1 e rejeita entrada malformada; serialização preserva o formato intercambiável, não configurações de UI.

Interfaces de repositório/serviço, assíncronas quando acessarem dados externos:

```dart
abstract interface class MusicLibraryRepository {
  Future<List<Track>> listTracks({String query = ''});
  Future<void> addTracks(Iterable<Track> tracks);
}
abstract interface class PlaylistRepository {
  Future<List<Playlist>> listPlaylists();
  Future<void> setFavorite(String trackId, bool favorite);
}
abstract interface class PlaybackService {
  Stream<PlaybackState> get states;
  Future<void> load(Track track);
  Future<void> play();
  Future<void> pause();
  Future<void> seek(Duration position);
}
abstract interface class ThemeRepository {
  Future<List<ThemeDefinition>> listThemes();
  Future<ThemeDefinition?> load(String id);
}
```

Os métodos podem ser ajustados no G2 para evitar interfaces artificiais; a regra é que widgets não acessem diretamente armazenamento ou plugin. Fakes usados pela demo/testes devem ter nomes e rótulos explícitos, não podem ser confundidos com armazenamento persistente ou reprodução real.

## Intercâmbio de temas

Desktop e mobile consomem a mesma fixture e o schema versionado em `docs/contracts/`. Tokens compartilhados fixados pelo coordenador: 29 nomes semânticos definidos no schema; valores `#RRGGBB`; tamanho máximo de arquivo 64 KiB; `schema_version` igual a 1; identificador por `^[a-z0-9][a-z0-9-]{0,63}$`; `name` de 1 a 60 caracteres e `author` opcional até 80, ambos sem controles C0/C1. Chaves desconhecidas, duplicadas, JSON excessivamente profundo e tokens ausentes/extras são rejeitados. Não há QSS, URL, código ou dados binários no tema.

Teste de contrato Dart deve ler `../../docs/contracts/theme-example.json` e rejeitar as fixtures de `docs/contracts/invalid/`; não manter cópia de cores que possa divergir. O parser traduz cores para `ColorScheme` e temas de componentes do Material 3, sem tentar reutilizar QSS. O modo inicial acompanha os presets definidos pelo desktop.

## Arquivos, identidades e persistência

O SQLite do desktop não será aberto diretamente pelo app: caminhos, locks, permissões e migrações pertencem à plataforma e não há contrato de sincronização definido. No primeiro estágio, repositórios são in-memory/demo. Quando a biblioteca local for implementada, um adaptador chama o seletor de arquivos oficial do sistema e copia/importa somente o necessário para armazenamento privado do app, ou mantém acesso concedido pelo SO por URI/bookmark documentado. Não persistir caminhos absolutos como identidade portátil.

Normalize texto de busca com Unicode NFC e comparação case-folded sem diacríticos, mantendo o texto de exibição original, em linha com a busca desktop. `Track.id` mobile deve ser estável dentro da biblioteca local; a identidade poderá derivar de UUID local + referência de documento concedida. Hash de conteúdo só será avaliado se necessário, pois custa I/O e não deve alegar equivalência entre sistemas. Playlist export/import e sincronização entre desktop e celular ficam para uma especificação futura.

Android deve usar o Storage Access Framework / `ACTION_OPEN_DOCUMENT` para seleção iniciada pelo usuário, sem pedir acesso amplo ao armazenamento para o caso básico. iOS deve usar `UIDocumentPickerViewController`, respeitando URLs com escopo de segurança e bookmarks se o acesso persistir. A API Flutter escolhida para isso precisa ser revisada na implementação, inclusive cobertura das versões Android/iOS e licenças.

## Verificação prevista no G2

Com SDK disponível: `flutter doctor -v`, `flutter pub get`, `dart format --output=none --set-exit-if-changed .`, `flutter analyze` e `flutter test` em `mobile/auralume_mobile/`. Testes devem cobrir contrato de tema compartilhado, modelos, estado indisponível do player, widgets de estados vazios e navegação. `flutter build apk --debug` só se JDK e Android SDK estiverem instalados/configurados. iOS requer macOS/Xcode. Nenhum desses resultados é afirmado por este documento.

Referências primárias consultadas:

- [Criar projeto Flutter com CLI](https://docs.flutter.dev/reference/create-new-app)
- [Arquitetura Flutter recomendada](https://docs.flutter.dev/app-architecture/guide)
- [Material 3 e ThemeData](https://docs.flutter.dev/release/breaking-changes/material-3-default)
- [Acessibilidade no Flutter](https://docs.flutter.dev/ui/accessibility/assistive-technologies)
- [Platform channels](https://docs.flutter.dev/platform-integration/platform-channels)
- [Android Storage Access Framework](https://developer.android.com/training/data-storage/shared/documents-files)
- [Apple UIDocumentPickerViewController](https://developer.apple.com/documentation/uikit/uidocumentpickerviewcontroller)
