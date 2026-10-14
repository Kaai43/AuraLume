# Integração HTTP local de fontes

`tests/test_sources_http.py` é um teste `integration` da implementação real de `SourceService` e do `yt-dlp` instalado. O teste gera um WAV PCM pequeno em memória e serve, por HTTP em `127.0.0.1` e porta efêmera, um redirect `/origin` → `/media/sample.wav`.

O teste verifica que `resolve(..., authorized=True)` mantém a URL `/origin` como origem persistente da faixa, retorna a URL final do stream, e que essa URL responde com `audio/wav` e conteúdo `RIFF/WAVE` legível. O diretório temporário de trabalho é conferido antes e depois da leitura para garantir que a resolução/consumo do stream não grava um download permanente. Não usa rede externa, credenciais ou cookies. A prova exercita resolução e transporte HTTP; não testa decodificação de áudio pelo libmpv.

Execução focada:

```sh
.venv/bin/python -m pytest -q -m integration tests/test_sources_http.py
```

Resultado nesta sessão: **1 passed**. A primeira tentativa no sandbox não conseguiu criar o socket (`PermissionError: Operation not permitted`). A mesma execução foi autorizada pelo mecanismo de elevação do ambiente, vinculou somente em loopback e passou em 0,92 s. Se o ambiente não permitir loopback, o teste deve permanecer marcado `integration` e a restrição deve ser reportada; não substitua o servidor real por mock para declarar essa integração verificada.

O teste segue a interface documentada de embedding do [yt-dlp](https://github.com/yt-dlp/yt-dlp#embedding-yt-dlp), exercida pelo próprio `SourceService`. Para reproduzir a prova, só é necessário rodar esse teste focado; não requer executar a suíte inteira.
