# ADR: estratégia futura de reprodução mobile

- Estado: avaliação para decisões posteriores; sem dependência escolhida para G2.
- Data: 2026-10-15.
- Contexto: a fundação Flutter precisa manter o player desacoplado e deixar claro que não reproduz áudio. Desktop usa Python/mpv e não será portado mecanicamente.

## Decisão provisória

Manter `PlaybackService` como contrato Dart independente de plugin. Quando o áudio real entrar em escopo, avaliar primeiro o ecossistema Flutter mantido e seu suporte atual a Android/iOS; comparar plugin de reprodução focado em engine mais integração separada de background/media session com uma implementação nativa via platform channels. Não escolher nem fixar pacote no G2.

Uma opção pública para avaliação é `just_audio` (Apache-2.0), voltado ao mecanismo de reprodução, com `audio_session` para configuração/interrupções e integração opcional `audio_service` (MIT) para reprodução em background e controles de sistema. Essas licenças são indícios por pacote; dependências transitivas, código nativo, codecs e obrigações de distribuição precisam ser auditados na versão efetivamente selecionada. Os repositórios e páginas de pacote podem mudar.

## Critérios de comparação

1. Reprodução de arquivos escolhidos pelo usuário, formatos e seeks confiáveis.
2. Reprodução em background, notificações/lock screen, headset e controles do sistema.
3. Política de interrupção por chamadas e navegação, foco de áudio e retomada configurável.
4. Bluetooth/saída externa, ciclo de desconexão e comportamento de bateria.
5. Document picker e permissões modernas com sandbox: SAF/URI no Android; URLs/bookmarks com security scope no iOS.
6. Frequência de manutenção, suporte às versões Flutter/Android/iOS alvo e comportamento em falha.
7. Licenças de todos os componentes e codecs, tamanho do app, testes de integração e possibilidade de remover plugin sem alterar domínio/UI.

## Limites de acesso a mídia

Escolha de arquivos deve partir de seletor do SO e conceder o menor acesso necessário. No Android, avaliar SAF (`ACTION_OPEN_DOCUMENT`) para acesso a documentos e URIs concedidas. No iOS, `UIDocumentPickerViewController` pode retornar URLs com security scope; a aplicação deve abrir e liberar o escopo corretamente e não guardar URL temporária como se fosse caminho permanente. Não pedir permissão ampla de biblioteca de mídia se o fluxo via seletor satisfaz a função.

## Consequências e pendências

- O G2 pode testar estado/modelo/UX sem engine ou permissões.
- Um futuro player deve emitir estado real e erros da plataforma; UI não pode inferir que um toque iniciou áudio.
- Antes de implementar, conferir versões atuais, changelogs, issues de manutenção e licenças diretamente nas fontes upstream; fazer uma prova curta de áudio com arquivo próprio em Android e iOS compatíveis.
- Precisam ser especificados: limites de versão OS, formatos garantidos, política de áudio em segundo plano, interrupções, persistência de URIs, cache/metadados/capas e experiência quando o acesso expira.
- Não declarar suporte de hardware/áudio audível sem teste em dispositivo real. Testes iOS e assinatura dependem de macOS/Xcode.

## Fontes consultadas

- [Flutter platform channels](https://docs.flutter.dev/platform-integration/platform-channels)
- [Android: acessar documentos e arquivos compartilhados](https://developer.android.com/training/data-storage/shared/documents-files)
- [Apple: UIDocumentPickerViewController](https://developer.apple.com/documentation/uikit/uidocumentpickerviewcontroller)
- [just_audio: recursos e integração](https://pub.dev/packages/just_audio)
- [Licença publicada de just_audio](https://pub.dev/packages/just_audio/license)
- [audio_service: áudio em background](https://pub.dev/packages/audio_service)
