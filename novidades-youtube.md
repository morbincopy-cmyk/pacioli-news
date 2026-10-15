# Projeto: Pacioli News (YouTube → Resumo → Blog)

> **Para o Claude Code:** este arquivo é a especificação completa do projeto. Leia tudo antes de começar. Siga as fases em ordem, pare nos checkpoints para eu validar e não pule a Fase 0.

---

## 1. Objetivo

Criar uma automação que roda no meu Mac, de hora em hora, e:

1. Detecta se o canal **Contabilidade Facilitada** publicou vídeo novo (só vídeos normais: **sem Shorts e sem lives**)
2. Obtém a transcrição do vídeo (legenda do YouTube primeiro; `mlx-whisper` local como reserva)
3. Gera um resumo detalhado em português do Brasil usando o próprio Claude Code em modo headless (`claude -p`)
4. Publica o resumo no blog **Pacioli News**, numa página **"Novidades do Dia DD/MM/AAAA"**

**Restrição principal: custo zero.** Nada de APIs pagas. O resumo sai do limite da minha assinatura do Claude; o resto é software livre e hospedagem gratuita.

---

## 2. Configuração definida

| Item | Valor |
|---|---|
| Canal | `https://www.youtube.com/@contabilidadefacilitada/videos` |
| Idioma | **Sempre português do Brasil** (legendas `pt-BR`/`pt`, Whisper com `language="pt"`, resumo em pt-BR) |
| Volume esperado | 2 a 3 vídeos por dia, em horários incertos |
| Execução | **De hora em hora, das 10h às 22h** (horário de Brasília). Deixar início e fim configuráveis em `config.json` |
| Shorts | **Não incluir** |
| Lives (ao vivo, agendadas ou gravadas) | **Não incluir** |
| Nome do site | **Pacioli News** |
| Repositório no GitHub | `pacioli-news` (público, exigência do GitHub Pages em conta gratuita) |
| Fuso horário | `America/Sao_Paulo` |

---

## 3. Ambiente já conhecido

- **Mac M2** (Apple Silicon, `arm64`)
- **Homebrew** instalado (versão 7.0.4)
- **mlx-whisper 0.4.3** instalado via pip no Python 3.9 do sistema, em `/Users/bernardoguttler/Library/Python/3.9/lib/python/site-packages`
- **GitHub CLI (`gh`)** instalado

---

## 4. Decisões técnicas (não reabrir sem motivo forte)

| Peça | Escolha | Motivo |
|---|---|---|
| Onde roda | Meu Mac, localmente | `mlx-whisper` já instalado; custo zero |
| Agendamento | `launchd` (LaunchAgent) com horários fixos | Executa a tarefa perdida quando o Mac acorda (o `cron` pula) |
| Detecção | `yt-dlp --flat-playlist` na aba **/videos** do canal | A aba /videos já separa Shorts (/shorts) e lives (/streams), então funciona como primeiro filtro |
| Transcrição 1 | Legenda pt-BR do YouTube via `yt-dlp` | Instantânea |
| Transcrição 2 (reserva) | `mlx-whisper` local | Para vídeos sem legenda; rápido no M2 |
| Resumo | `claude -p` (Claude Code headless) | Usa a assinatura, sem custo extra |
| Site | Blog estático em HTML/CSS/JS puros no **GitHub Pages** | Gratuito, sem etapa de build, atualiza a cada `git push` |
| Scripts | Python 3 (o mesmo interpretador onde o `mlx-whisper` está instalado) + shell | Evita instalar outro Python |

---

## 5. Fase 0 — Verificar o ambiente antes de escrever código

Rode as verificações abaixo e me mostre o resultado **antes de instalar qualquer coisa**:

- `which python3` e `python3 -c "import mlx_whisper; print('ok')"`: confirmar qual interpretador enxerga o `mlx-whisper`. Os scripts devem usar **esse** Python, com caminho absoluto.
- Onde está o executável de linha de comando do mlx-whisper (provavelmente em `~/Library/Python/3.9/bin/`, que costuma ficar fora do `PATH`). Preferir chamar pela API Python (`mlx_whisper.transcribe(...)`) para não depender do `PATH`.
- `yt-dlp --version` e `ffmpeg -version` (o `ffmpeg` é obrigatório para extrair áudio e para o Whisper)
- `git --version` e `gh auth status`
- `claude -p "responda só: ok"` funciona fora do modo interativo?

Instale só o que faltar (via Homebrew) e me diga antes o que vai instalar.

> **Nota sobre o Python 3.9:** é antigo, mas suficiente. Não atualize nem crie outro ambiente sem me consultar, para não perder o `mlx-whisper` que já funciona.

---

## 6. Estrutura de pastas

```
pacioli-news/
├── CLAUDE.md                  # resumo deste projeto, para sessões futuras
├── config.json                # canal, horários, idioma, filtros, caminhos
├── run.sh                     # ponto de entrada chamado pelo launchd
├── pipeline/
│   ├── detect.py              # lista vídeos novos da aba /videos e aplica filtros
│   ├── transcribe.py          # legenda pt-BR via yt-dlp → fallback mlx-whisper
│   ├── summarize.sh           # chama claude -p com o prompt
│   ├── publish.py             # grava/atualiza o post do dia e o índice
│   └── prompts/
│       └── resumo.md          # prompt do resumo (editável por mim)
├── state/
│   └── processed.json         # IDs já processados e IDs em espera
├── work/                      # transcrições e áudios temporários (no .gitignore)
├── logs/                      # um log por execução (no .gitignore)
└── site/                      # o que vai para o GitHub Pages
    ├── index.html             # home do blog
    ├── post.html              # página de um dia
    ├── sobre.html             # sobre o Pacioli News e crédito ao canal
    ├── assets/                # CSS, JS
    └── posts/
        ├── index.json         # lista de dias publicados (data, título, resumo curto, nº de vídeos)
        └── 2026-10-15.md      # um arquivo por dia
```

---

## 7. Fases de implementação

### Fase 1 — Detecção

- Listar os vídeos mais recentes da aba `/videos` com `yt-dlp --flat-playlist` (os últimos 15 bastam).
- Para cada vídeo ainda não processado, buscar os metadados completos (`yt-dlp --dump-json`) e aplicar os filtros:
  - **Shorts:** excluir se a URL contiver `/shorts/` ou se a duração for de até 3 minutos.
  - **Lives:** excluir se `live_status` for `is_live`, `was_live` ou `post_live`. Excluídos vão para `processed.json` com o motivo, para não serem reavaliados.
  - **Estreias agendadas** (`is_upcoming`): não processar ainda; deixar em espera e reavaliar na próxima hora.
  - Se um vídeo normal estiver sem legenda **e** tiver sido publicado há menos de 1 hora, deixar em espera uma rodada (a legenda automática costuma demorar). Na rodada seguinte, seguir para o Whisper se ainda não houver legenda.
- **Primeira execução:** não processar o histórico. Marcar como processados todos os vídeos atuais, exceto o mais recente (que vira o post de teste).

✅ **Checkpoint:** me mostre a lista detectada, com o que foi aceito, excluído (e por quê) e deixado em espera.

### Fase 2 — Transcrição

Ordem de tentativa:

1. Legenda manual em `pt-BR`/`pt`
2. Legenda automática em `pt`
3. `mlx-whisper` local: baixar só o áudio com `yt-dlp -x --audio-format m4a` e transcrever com `language="pt"` e o modelo `mlx-community/whisper-large-v3-turbo` (avisar que o primeiro uso baixa o modelo, cerca de 1,5 GB)

Requisitos:

- Converter a legenda (`.vtt`/`.srt`) em texto limpo: sem timestamps, sem tags e sem as linhas repetidas típicas da legenda automática.
- Salvar em `work/<video_id>.txt`.
- Apagar o áudio depois de transcrever.
- Registrar no log qual método foi usado.

✅ **Checkpoint:** me mostre os primeiros parágrafos da transcrição do vídeo de teste.

### Fase 3 — Resumo com `claude -p`

- `summarize.sh` envia a transcrição via stdin para o `claude -p`, junto com o prompt de `prompts/resumo.md`, e captura a resposta em stdout.
- **Segurança:** o resumo não precisa de nenhuma ferramenta. Rodar sem liberar ferramentas, com o mínimo de turnos. **Não usar `--dangerously-skip-permissions`.** Consulte `claude --help` para os flags corretos da versão instalada.
- Se a transcrição for muito longa, dividir em partes, resumir cada uma e depois consolidar.
- Validar a saída: tem que começar com o título esperado e não pode vir vazia. Se falhar, tentar mais uma vez; se falhar de novo, registrar erro, **não marcar como processado** (para tentar na próxima hora) e não publicar.

**Prompt inicial** (`prompts/resumo.md`), que vou ajustar no checkpoint:

```
Você vai receber a transcrição de um vídeo do canal Contabilidade Facilitada,
sobre contabilidade, tributação e rotina de escritórios contábeis no Brasil.
Escreva um resumo detalhado em português do Brasil, em Markdown, neste formato:

## {título do vídeo}

**Em uma frase:** a ideia central do vídeo.

### Principais pontos
Os pontos mais importantes, em ordem, com o contexto necessário para entender
cada um sem ter visto o vídeo.

### Detalhes que valem atenção
Prazos, alíquotas, números, normas, obrigações acessórias, ferramentas ou
recomendações citadas.

### Para quem é útil
Uma ou duas frases (ex.: contadores, donos de escritório, empreendedores).

Regras:
- Não invente nada que não esteja na transcrição, principalmente números,
  prazos e nomes de leis ou obrigações.
- Se um trecho estiver confuso (erro de transcrição), omita em vez de chutar.
- Não reproduza longos trechos literais; escreva com suas palavras.
- Não inclua o link; ele será adicionado depois.
```

✅ **Checkpoint:** me mostre o resumo do vídeo de teste antes de seguir.

### Fase 4 — Blog Pacioli News

Um blog simples e limpo, com cara de blog de verdade:

- **HTML, CSS e JS puros, sem etapa de build.** O GitHub Pages serve os arquivos como estão.
- **Cabeçalho** com o nome "Pacioli News" e uma linha de descrição (ex.: "Os vídeos de contabilidade do dia, resumidos"). Menu com "Início" e "Sobre".
- **Home (`index.html`):** lê `posts/index.json` e lista os posts em ordem do mais recente para o mais antigo, cada um com título ("Novidades do Dia DD/MM/AAAA"), data, quantidade de vídeos e um trecho de prévia. Paginação simples a partir de 10 posts.
- **Post (`post.html?dia=AAAA-MM-DD`):** carrega o `.md` do dia e renderiza com uma biblioteca de Markdown carregada de CDN com versão fixa (ex.: `marked`). Links "post anterior / próximo" no rodapé.
- **Sobre (`sobre.html`):** explica que o Pacioli News resume automaticamente os vídeos do canal Contabilidade Facilitada, com link para o canal.
- **Visual:** tipografia boa para leitura, coluna de texto centralizada, sem excesso de elementos. Responsivo e com modo claro e escuro.
- **Rodapé** em todas as páginas com crédito ao canal original.

**Regras de conteúdo:**

- Um post por dia, com o título **"Novidades do Dia DD/MM/AAAA"**.
- O dia de um vídeo é a **data de publicação no YouTube**, no fuso `America/Sao_Paulo`.
- Como os vídeos saem em horários diferentes, **cada execução acrescenta o vídeo novo ao post do dia** (criando o post se for o primeiro do dia). Os vídeos ficam em ordem de publicação dentro do post.
- Se um vídeo de ontem só for processado hoje às 10h, ele entra no post de **ontem**, que é atualizado.
- Cada seção de vídeo termina com: link para o vídeo original, nome do canal e horário de publicação.
- **Não publicar a transcrição completa**, só o resumo com crédito e link.

✅ **Checkpoint:** abrir o site localmente (`python3 -m http.server` dentro de `site/`) e me mostrar a home e um post.

### Fase 5 — Publicação no GitHub Pages

- Criar o repositório público `pacioli-news` com `gh`.
- Configurar o GitHub Pages para servir a pasta `site/` (ou a branch adequada).
- Garantir que o `git push` funcione sem senha interativa (`gh auth setup-git` ou SSH).
- `publish.py` grava ou atualiza o post do dia, atualiza `posts/index.json` e `state/processed.json`, faz commit com a mensagem `novidades: AAAA-MM-DD (+N vídeo)` e dá push.

✅ **Checkpoint:** me passar a URL pública do Pacioli News com o post de teste no ar.

### Fase 6 — Agendamento com `launchd`

- Criar `~/Library/LaunchAgents/com.bernardo.pacioli-news.plist` com `StartCalendarInterval` contendo uma entrada para cada hora cheia **das 10h às 22h** (lidas de `config.json`; gerar o plist a partir dele).
- `run.sh` deve:
  - Definir um `PATH` completo (o `launchd` não carrega o do terminal): incluir `/opt/homebrew/bin`, `/usr/local/bin`, `~/Library/Python/3.9/bin` e o caminho do `claude`.
  - Usar caminhos absolutos em tudo, inclusive o do Python que tem o `mlx-whisper`.
  - Gravar log em `logs/AAAA-MM-DD_HHMM.log` e apagar logs com mais de 30 dias.
  - Impedir duas execuções ao mesmo tempo (arquivo de lock), já que uma transcrição pelo Whisper pode passar de uma hora em casos raros.
  - Em caso de erro, mostrar uma **notificação do macOS** (`osascript -e 'display notification ...'`).
  - Se não houver vídeo novo, terminar em silêncio e rápido.
- Carregar com `launchctl` e testar disparando manualmente (`launchctl kickstart`).
- Verificar se o `claude -p` consegue autenticar quando chamado pelo `launchd` (fora do terminal). Se não conseguir, investigar e me explicar as opções.
- Se o macOS bloquear acesso a arquivos, me orientar sobre as permissões em Ajustes do Sistema → Privacidade e Segurança.

✅ **Checkpoint:** mostrar o log de uma execução disparada pelo `launchd`.

### Fase 7 — Documentação

Gerar o `CLAUDE.md` do projeto, curto, com:

- O que o projeto faz e o fluxo
- Como rodar manualmente: `./run.sh`
- Como processar um vídeo específico: `./run.sh --video <URL>`
- Como testar sem publicar: `./run.sh --dry-run`
- Como mudar os horários, o canal e o prompt
- Como pausar e reativar o agendamento
- Manutenção: quando o download falhar, rodar `brew upgrade yt-dlp` primeiro

---

## 8. Critérios de pronto

- [ ] Um vídeo novo no canal vira post no Pacioli News em até 1 hora, sem eu fazer nada
- [ ] Shorts e lives nunca aparecem no site
- [ ] Vários vídeos do mesmo dia entram no mesmo post, em ordem
- [ ] Vídeo sem legenda é transcrito pelo `mlx-whisper`
- [ ] Nenhum vídeo é processado duas vezes
- [ ] Falha no resumo não perde o vídeo: ele é tentado de novo na hora seguinte
- [ ] Falhas geram notificação no Mac e log legível
- [ ] Custo zero: nenhuma API paga
- [ ] `--dry-run` e `--video` funcionam
- [ ] `CLAUDE.md` explica como operar

---

## 9. Fora do escopo (por enquanto)

- Rodar na nuvem sem depender do Mac
- Mais de um canal
- Newsletter ou envio por e-mail
- Comentários, busca ou tags no blog

Se algo aqui não for viável do jeito descrito, **me avise e proponha alternativa antes de implementar outra coisa.**
