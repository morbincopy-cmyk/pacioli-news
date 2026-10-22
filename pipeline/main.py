"""Orquestra uma execução: detectar -> transcrever -> resumir -> publicar.

Chamado pelo run.sh. Opções:
    --dry-run        não publica, não faz commit e não altera o estado
    --video <URL>    processa só esse vídeo (mesmo que já tenha sido processado)

Código de saída diferente de zero quando algum vídeo falhou (o run.sh notifica).
"""
import sys

from common import CONFIG, WORK_DIR, empty_state, load_state, log, now, save_state
from detect import EXCLUDE, classify, detect, fetch_meta, print_report, summarize_meta
from publish import publish
from summary import summarize
from transcribe import transcribe, video_id_from


def parse_args(argv):
    dry_run = "--dry-run" in argv
    video = None
    if "--video" in argv:
        i = argv.index("--video")
        if i + 1 >= len(argv):
            raise SystemExit("uso: run.sh --video <URL>")
        video = argv[i + 1]
    return dry_run, video


def single_video(arg):
    vid = video_id_from(arg)
    meta = fetch_meta(vid)
    decision, reason = classify({"url": arg}, meta, None, now())
    if decision == EXCLUDE:
        log(f"Aviso: {vid} seria excluído na detecção ({reason}); processando mesmo assim, como pedido")
    return summarize_meta(meta)


def mark_failure(state, info, error):
    prev = state["pending"].get(info["id"]) or {}
    state["pending"][info["id"]] = {
        "reason": "falha no processamento", "title": info["title"],
        "failures": prev.get("failures", 0) + 1, "error": str(error)[:500],
        "since": prev.get("since", now().isoformat(timespec="seconds")),
    }


def cached_transcript(video_id):
    """Transcrição de uma tentativa anterior que falhou depois de transcrever."""
    txt, meta = WORK_DIR / f"{video_id}.txt", WORK_DIR / f"{video_id}.method"
    if txt.exists() and meta.exists() and txt.stat().st_size > 0:
        return txt, meta.read_text(encoding="utf-8").strip()
    return None


def process(info, state, dry_run, reuse=True):
    log(f"Processando {info['id']}: {info['title']}")
    cached = cached_transcript(info["id"]) if reuse else None
    if cached:
        transcript, method = cached
        log(f"Reaproveitando a transcrição da tentativa anterior ({method})")
    else:
        transcript, method = transcribe(info["id"])
    summary_md = summarize(transcript, info["title"])
    if dry_run:
        out = WORK_DIR / f"{info['id']}.summary.md"
        out.write_text(summary_md, encoding="utf-8")
        log(f"dry-run: resumo salvo em {out}, nada publicado")
        return
    publish(state, [(info, summary_md, method)])
    transcript.unlink(missing_ok=True)
    (WORK_DIR / f"{info['id']}.method").unlink(missing_ok=True)


def main(argv):
    dry_run, video = parse_args(argv)
    WORK_DIR.mkdir(exist_ok=True)
    state = load_state()

    if video:
        state = state or empty_state()
        to_process = [single_video(video)]
    else:
        to_process, report, state = detect(state, dry_run=dry_run)
        if not report:
            log("Nenhum vídeo novo.")
            return 0
        print_report(report)

    failures = 0
    for info in to_process:
        try:
            process(info, state, dry_run, reuse=not video)
        except Exception as e:
            failures += 1
            log(f"ERRO em {info['id']}: {e}")
            if not dry_run:
                # Fica em espera, sem ser marcado como processado: tenta de novo na próxima hora.
                mark_failure(state, info, e)
                save_state(state)

    log(f"Fim: {len(to_process) - failures} ok, {failures} com erro" + (" (dry-run)" if dry_run else ""))
    return 1 if failures else 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except Exception as e:  # falha geral (rede, YouTube fora do ar...): log legível e código de erro
        log(f"ERRO: {e}")
        sys.exit(1)
