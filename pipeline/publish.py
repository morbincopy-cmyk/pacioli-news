"""Publicação: grava o resumo, reconstrói o post do dia e o índice, faz commit e push.

O post de cada dia é sempre reconstruído a partir de state/summaries/<id>.md e dos
metadados em state/processed.json. Assim os vídeos ficam em ordem de publicação e
um vídeo atrasado entra no post do dia certo.

Uso isolado:
    python3 pipeline/publish.py <video_id> [--no-git]   # publica o resumo de work/<id>.summary.md
    python3 pipeline/publish.py --rebuild [--no-git]    # reconstrói o site a partir de state/summaries
"""
import html
import re
import sys

from common import (CONFIG, POSTS_DIR, ROOT, SUMMARIES_DIR, WORK_DIR, empty_state,
                    load_state, local_dt, log, now, run, save_state, write_json)

WEEKDAYS = ["segunda-feira", "terça-feira", "quarta-feira", "quinta-feira", "sexta-feira", "sábado", "domingo"]


def br_date(iso):
    y, m, d = iso.split("-")
    return f"{d}/{m}/{y}"


def day_title(iso):
    return f"Novidades do Dia {br_date(iso)}"


def one_liner(summary_md):
    m = re.search(r"\*\*Em uma frase:\*\*\s*(.+)", summary_md)
    return m.group(1).strip() if m else ""


def source_card(video):
    """Bloco que fecha cada vídeo: link, canal e horário de publicação."""
    when = local_dt(video["timestamp"])
    url = html.escape(video["url"])
    channel = html.escape(video["channel"])
    return (
        '<div class="fonte">\n'
        f'<a class="fonte-thumb" href="{url}" target="_blank" rel="noopener">'
        f'<img src="https://i.ytimg.com/vi/{video["id"]}/mqdefault.jpg" alt="" loading="lazy"></a>\n'
        f'<div class="fonte-texto"><a href="{url}" target="_blank" rel="noopener">Assistir ao vídeo original no YouTube</a>'
        f'<span>{channel} · publicado em {when:%d/%m/%Y} às {when:%H}h{when:%M}</span></div>\n'
        "</div>"
    )


def published_videos(state):
    return [dict(v, id=vid) for vid, v in state["processed"].items() if v.get("status") == "published"]


def build_day(date, state):
    videos = sorted((v for v in published_videos(state) if v["date"] == date), key=lambda v: v["timestamp"])
    parts = ["<!-- Gerado por pipeline/publish.py a partir de state/summaries. Não edite à mão. -->"]
    for v in videos:
        summary = (SUMMARIES_DIR / f"{v['id']}.md").read_text(encoding="utf-8").strip()
        # Linhas em branco em volta do Markdown: o <section> é um bloco HTML e o
        # conteúdo de dentro continua sendo interpretado como Markdown.
        parts.append(f'<section class="video" id="v-{v["id"]}">\n\n{summary}\n\n{source_card(v)}\n\n</section>')
    (POSTS_DIR / f"{date}.md").write_text("\n\n".join(parts) + "\n", encoding="utf-8")
    return videos


def build_index(state):
    days = {}
    for v in published_videos(state):
        days.setdefault(v["date"], []).append(v)
    index = []
    for date in sorted(days, reverse=True):
        videos = sorted(days[date], key=lambda v: v["timestamp"])
        first = (SUMMARIES_DIR / f"{videos[0]['id']}.md").read_text(encoding="utf-8")
        y, m, d = map(int, date.split("-"))
        index.append({
            "date": date,
            "title": day_title(date),
            "weekday": WEEKDAYS[local_dt(videos[0]["timestamp"]).weekday()],
            "count": len(videos),
            "excerpt": one_liner(first),
            "videos": [{"id": v["id"], "title": v["title"],
                        "time": local_dt(v["timestamp"]).strftime("%Hh%M")} for v in videos],
        })
    write_json(POSTS_DIR / "index.json", index)
    return index


def record(state, info, summary_md, method):
    """Grava o resumo e marca o vídeo como publicado no estado."""
    SUMMARIES_DIR.mkdir(parents=True, exist_ok=True)
    (SUMMARIES_DIR / f"{info['id']}.md").write_text(summary_md, encoding="utf-8")
    state["pending"].pop(info["id"], None)
    state["processed"][info["id"]] = {
        "status": "published", "title": info["title"], "date": info["date"],
        "timestamp": info["timestamp"], "url": info["url"], "channel": info["channel"],
        "transcription": method, "at": now().isoformat(timespec="seconds"),
    }


def git(*args):
    r = run([CONFIG["paths"]["git"], "-C", str(ROOT), *args], timeout=300)
    if r.returncode != 0:
        raise RuntimeError(f"git {args[0]} falhou: {(r.stderr or r.stdout).strip()}")
    return r.stdout


def commit_and_push(changed_dates=None, msg=None):
    """Commit com 'novidades: AAAA-MM-DD (+N vídeo)' (ou `msg`) e push."""
    git("add", "-A", "site", "state")
    if not git("status", "--porcelain", "site", "state").strip():
        log("Nada novo para publicar no git")
        return
    msg = msg or "; ".join(f"novidades: {d} (+{n} vídeo{'s' if n > 1 else ''})" for d, n in sorted(changed_dates.items()))
    git("commit", "-m", msg)
    git("push", CONFIG["publish"]["git_remote"], CONFIG["publish"]["git_branch"])
    log(f"Publicado: {msg}")


def publish(state, items, use_git=True):
    """items: lista de (info, resumo_md, método). Atualiza estado, posts, índice e git."""
    changed = {}
    for info, summary_md, method in items:
        record(state, info, summary_md, method)
        changed[info["date"]] = changed.get(info["date"], 0) + 1
    for date in changed:
        n = len(build_day(date, state))
        log(f"Post {day_title(date)}: {n} vídeo(s)")
    build_index(state)
    save_state(state)
    if use_git:
        commit_and_push(changed)


def rebuild(state, use_git=True):
    """Reconstrói todos os posts e o índice (ex.: depois de editar state/summaries à mão)."""
    for date in sorted({v["date"] for v in published_videos(state)}):
        build_day(date, state)
    build_index(state)
    if use_git:
        commit_and_push(msg="novidades: posts reconstruídos")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    if sys.argv[1] == "--rebuild":
        rebuild(load_state() or empty_state(), use_git="--no-git" not in sys.argv)
        sys.exit(0)
    from detect import fetch_meta, summarize_meta
    vid = sys.argv[1]
    info = summarize_meta(fetch_meta(vid))
    summary = (WORK_DIR / f"{vid}.summary.md").read_text(encoding="utf-8")
    publish(load_state() or empty_state(), [(info, summary, "manual")], use_git="--no-git" not in sys.argv)
