"""Detecta vídeos novos na aba /videos do canal e aplica os filtros.

Uso isolado (mostra o relatório):
    python3 pipeline/detect.py [--dry-run]
"""
import json
import sys

from common import (CONFIG, empty_state, load_state, local_dt, log,
                    now, save_state, watch_url, ytdlp)

DET = CONFIG["detection"]
LIVE_STATUSES = {"is_live", "was_live", "post_live"}

ACCEPT, EXCLUDE, WAIT = "aceito", "excluído", "em espera"


def list_recent():
    """IDs dos vídeos mais recentes da aba /videos, do mais novo para o mais antigo."""
    out = ytdlp([
        "--flat-playlist", "--playlist-end", str(DET["playlist_end"]),
        "--print", "%(id)s\t%(url)s", CONFIG["channel_url"],
    ])
    entries = []
    for line in out.splitlines():
        if "\t" in line:
            vid, url = line.split("\t", 1)
            entries.append({"id": vid, "url": url})
    if not entries:
        raise RuntimeError("a aba /videos voltou vazia")
    return entries


def fetch_meta(video_id):
    """Metadados completos do vídeo."""
    # --ignore-no-formats-error: lives e estreias agendadas não têm formatos ainda,
    # e sem isso o yt-dlp falha em vez de devolver os metadados.
    return json.loads(ytdlp(["--skip-download", "--ignore-no-formats-error", "--dump-json", watch_url(video_id)]))


def has_pt_captions(meta):
    subs = meta.get("subtitles") or {}
    auto = meta.get("automatic_captions") or {}
    manual = CONFIG["transcription"]["manual_sub_langs"]
    automatic = CONFIG["transcription"]["auto_sub_langs"]
    return any(k in subs for k in manual) or any(k in auto for k in automatic)


def summarize_meta(meta):
    ts = meta.get("timestamp") or meta.get("release_timestamp")
    return {
        "id": meta["id"],
        "title": meta.get("title") or meta["id"],
        "url": watch_url(meta["id"]),
        "channel": meta.get("channel") or CONFIG["channel_name"],
        "timestamp": ts,
        "date": local_dt(ts).strftime("%Y-%m-%d") if ts else None,
        "duration": meta.get("duration"),
        "has_captions": has_pt_captions(meta),
    }


def classify(entry, meta, pending, current):
    """Devolve (decisão, motivo)."""
    urls = " ".join(str(x) for x in (entry.get("url"), meta.get("webpage_url"), meta.get("original_url")))
    if "/shorts/" in urls:
        return EXCLUDE, "Short (URL /shorts/)"

    live = meta.get("live_status")
    if live in LIVE_STATUSES:
        return EXCLUDE, f"live ({live})"
    if live == "is_upcoming":
        return WAIT, "estreia agendada"

    duration = meta.get("duration")
    if duration is not None and duration <= DET["shorts_max_seconds"]:
        return EXCLUDE, f"Short (duração {duration}s)"

    # A transcrição começa pelo Whisper; a legenda é só reserva, então não há o que esperar.
    return ACCEPT, "vídeo normal" + ("" if has_pt_captions(meta) else " (sem legenda de reserva)")


def detect(state=None, dry_run=False):
    """Roda a detecção. Devolve (aceitos, relatório, estado).

    Aceitos não são gravados no estado: só viram 'processados' depois de publicados,
    para que uma falha faça o vídeo ser tentado de novo na hora seguinte.
    """
    first_run = state is None
    if first_run:
        state = empty_state()
    processed, pending = state["processed"], state["pending"]
    current = now()
    stamp = current.isoformat(timespec="seconds")

    accepted, report = [], []
    for entry in list_recent():
        vid = entry["id"]
        if vid in processed:
            continue
        prev = pending.get(vid)
        try:
            meta = fetch_meta(vid)
        except Exception as e:  # vídeo privado, para membros, erro de rede...
            failures = (prev or {}).get("failures", 0) + 1
            if failures >= DET["max_metadata_failures"]:
                pending.pop(vid, None)
                processed[vid] = {"status": "excluded", "reason": f"metadados indisponíveis: {e}", "at": stamp}
                report.append((vid, vid, EXCLUDE, f"metadados indisponíveis após {failures} tentativas"))
            else:
                pending[vid] = {"reason": "erro de metadados", "failures": failures, "since": (prev or {}).get("since", stamp)}
                report.append((vid, vid, WAIT, f"erro ao ler metadados ({e})"))
            continue

        info = summarize_meta(meta)
        decision, reason = classify(entry, meta, prev, current)
        report.append((vid, info["title"], decision, reason))

        if decision == EXCLUDE:
            pending.pop(vid, None)
            processed[vid] = {"status": "excluded", "reason": reason, "title": info["title"],
                              "date": info["date"], "at": stamp}
        elif decision == WAIT:
            pending[vid] = {"reason": reason, "title": info["title"], "since": (prev or {}).get("since", stamp)}
        else:
            if prev and prev.get("reason") != "falha no processamento":
                pending.pop(vid, None)
            accepted.append(info)

    if first_run:
        # Não processar o histórico: só o mais recente vira o post de teste.
        accepted.sort(key=lambda v: v["timestamp"] or 0, reverse=True)
        test, history = accepted[:1], accepted[1:]
        history_ids = {v["id"] for v in history}
        for v in history:
            processed[v["id"]] = {"status": "history", "reason": "histórico (primeira execução)",
                                  "title": v["title"], "date": v["date"], "at": stamp}
        report = [(vid, title, "histórico" if vid in history_ids else d, "primeira execução" if vid in history_ids else r)
                  for vid, title, d, r in report]
        accepted = test

    accepted.sort(key=lambda v: v["timestamp"] or 0)
    if not dry_run:
        save_state(state)
    return accepted, report, state


def print_report(report):
    if not report:
        log("Nenhum vídeo novo.")
        return
    width = max(len(d) for _, _, d, _ in report)
    for vid, title, decision, reason in report:
        print(f"  {decision:<{width}}  {vid}  {title}  [{reason}]")


if __name__ == "__main__":
    dry = "--dry-run" in sys.argv
    acc, rep, _ = detect(load_state(), dry_run=dry)
    print_report(rep)
    log(f"{len(acc)} vídeo(s) para processar" + (" (dry-run: estado não salvo)" if dry else ""))
