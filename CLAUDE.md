# Pacioli News

Automação que roda no Mac de hora em hora (10h–22h, Brasília). Quando o canal **Contabilidade Facilitada** publica um vídeo novo, ela transcreve, resume em pt-BR e publica no blog https://morbincopy-cmyk.github.io/pacioli-news/, no post "Novidades do Dia DD/MM/AAAA". Custo zero: nada de API paga.

Especificação completa e decisões: `novidades-youtube.md`.

## Fluxo

`launchd` → `run.sh` → `pipeline/main.py`:

1. **Detecção** (`detect.py`): os últimos 15 da aba `/videos` via `yt-dlp`. Shorts (URL `/shorts/` ou ≤ 3 min) e lives são excluídos e registrados. Estreias agendadas ficam em espera.
2. **Transcrição** (`transcribe.py`): `mlx-whisper` local primeiro; se falhar, legenda manual pt-BR/pt e depois a automática do YouTube. Resultado em `work/<id>.txt`.
3. **Resumo** (`summary.py` + `summarize.sh`): `claude -p` sem ferramentas, com o prompt `pipeline/prompts/resumo.md`. Transcrições longas são resumidas em partes (`prompts/parte.md`). Duas tentativas.
4. **Publicação** (`publish.py`): grava `state/summaries/<id>.md` e reconstrói `site/posts/<dia>.md` e `site/posts/index.json`. Depois faz commit `novidades: AAAA-MM-DD (+N vídeo)` e push. O GitHub Actions (`.github/workflows/pages.yml`) publica `site/` em menos de 1 min.

O dia do post é a data de publicação no YouTube (America/Sao_Paulo). Um vídeo que falha não é marcado como processado: fica em `pending` no `state/processed.json` e é tentado de novo na hora seguinte, com notificação no Mac.

## Operar

| Tarefa | Comando |
|---|---|
| Rodar agora | `./run.sh` |
| Processar um vídeo específico | `./run.sh --video <URL>` (reprocessa mesmo se já publicado) |
| Testar sem publicar | `./run.sh --dry-run` (pode combinar com `--video`; o resumo fica em `work/<id>.summary.md`) |
| Ver logs | `logs/AAAA-MM-DD_HHMM.log` (um por execução, apagados após 30 dias) |
| Pausar / reativar o agendamento | `python3 pipeline/schedule.py pause` / `resume` |
| Disparar pelo launchd / ver status | `python3 pipeline/schedule.py run` / `status` |

## Mudar

- **Horários**: `schedule.start_hour` / `end_hour` no `config.json`, depois `python3 pipeline/schedule.py install` (regera o plist em `~/Library/LaunchAgents/com.bernardo.pacioli-news.plist`).
- **Canal**: `channel_url` e `channel_name` no `config.json`. Num canal novo, apague `state/processed.json` para a primeira execução marcar o histórico em vez de processá-lo.
- **Prompt do resumo**: `pipeline/prompts/resumo.md`. Mantenha o título `## {título do vídeo}` e a seção `**Em uma frase:**`: a validação exige os dois, e a home usa a frase como prévia.
- **Ordem da transcrição**: `transcription.order` no `config.json`.
- **Visual do blog**: `site/assets/style.css` e `site/assets/app.js` (HTML/CSS/JS puros, sem build).

## Ambiente e cuidados

- O projeto fica em `~/pacioli-news`; `~/Desktop/Pacioli-News` é só um atalho. **Não mova de volta para a Área de Trabalho**: o macOS bloqueia o acesso do `launchd` a ela (`Operation not permitted`).
- Python: `/usr/bin/python3` (3.9, onde o `mlx-whisper` está instalado). Não atualize nem troque de ambiente.
- O Mac precisa estar ligado e com sessão aberta. Se estiver dormindo, a execução perdida roda quando ele acordar.
- Não edite `site/posts/*.md` à mão: eles são reconstruídos a partir de `state/summaries/`. Para corrigir um resumo, edite `state/summaries/<id>.md` e rode `python3 pipeline/publish.py --rebuild` (reconstrói e publica), ou gere de novo com `./run.sh --video <URL>`.

## Manutenção

- **Download do YouTube falhou** (erros do `yt-dlp` no log): rode `brew upgrade yt-dlp` primeiro. O YouTube muda com frequência e o `yt-dlp` acompanha.
- **`claude -p` falhou**: rode `claude -p "responda só: ok"` no terminal para ver se a sessão expirou ou o limite da assinatura acabou.
- **Push falhou**: `gh auth status` e `gh auth setup-git`.
- **Execução travada**: o lock fica em `state/run.lock/`. Um lock de processo morto é removido sozinho.
