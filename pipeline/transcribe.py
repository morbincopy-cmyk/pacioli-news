"""Transcrição: mlx-whisper local primeiro; legenda do YouTube como reserva.

A ordem vem de config.json (transcription.order). Resultado em work/<video_id>.txt.

Uso isolado:
    python3 pipeline/transcribe.py <video_id ou URL> [--method whisper|manual_subs|auto_subs]
"""
import re
import sys

from common import CONFIG, WORK_DIR, log, watch_url, ytdlp

TR = CONFIG["transcription"]
PARAGRAPH_WORDS = 120


def to_paragraphs(pieces):
    """Junta trechos em parágrafos de ~120 palavras, quebrando em fim de frase quando possível."""
    paragraphs, current, words = [], [], 0
    for piece in pieces:
        piece = " ".join(piece.split())
        if not piece:
            continue
        current.append(piece)
        words += len(piece.split())
        ends_sentence = piece[-1] in ".!?"
        if (words >= PARAGRAPH_WORDS and ends_sentence) or words >= PARAGRAPH_WORDS * 2:
            paragraphs.append(" ".join(current))
            current, words = [], 0
    if current:
        paragraphs.append(" ".join(current))
    return "\n\n".join(paragraphs)


# ---------- Whisper ----------

def via_whisper(video_id):
    WORK_DIR.mkdir(exist_ok=True)
    for old in WORK_DIR.glob(f"{video_id}.audio.*"):
        old.unlink()
    log("Whisper: baixando o áudio")
    ytdlp(["-f", "bestaudio", "-x", "--audio-format", "m4a",
           "-o", str(WORK_DIR / f"{video_id}.audio.%(ext)s"), watch_url(video_id)], timeout=1800)
    audio = WORK_DIR / f"{video_id}.audio.m4a"
    if not audio.exists():
        raise RuntimeError("o áudio não foi baixado")
    try:
        import mlx_whisper  # importado aqui: carregar o MLX só quando for usar
        log(f"Whisper: transcrevendo com {TR['whisper_model']} (o primeiro uso baixa o modelo, ~1,5 GB)")
        result = mlx_whisper.transcribe(
            str(audio), path_or_hf_repo=TR["whisper_model"],
            language=TR["whisper_language"], verbose=None,
        )
    finally:
        audio.unlink(missing_ok=True)
    return to_paragraphs(seg["text"] for seg in result.get("segments", []))


# ---------- Legendas do YouTube ----------

TAG_RE = re.compile(r"<[^>]+>")
TIMING_RE = re.compile(r"^\d{2}:\d{2}(:\d{2})?[.,]\d{3}\s+-->")


def clean_vtt(raw):
    """Texto limpo de um .vtt/.srt: sem cabeçalho, timestamps, tags nem as linhas
    repetidas da legenda automática (que 'rola' repetindo a linha anterior)."""
    pieces, recent = [], []
    for line in raw.splitlines():
        line = line.strip()
        if (not line or line == "WEBVTT" or line.isdigit() or TIMING_RE.match(line)
                or line.startswith(("Kind:", "Language:", "NOTE", "STYLE"))):
            continue
        text = " ".join(TAG_RE.sub("", line).replace("&nbsp;", " ").replace("&amp;", "&").split())
        if not text or text in recent:
            continue
        pieces.append(text)
        recent = (recent + [text])[-3:]
    return to_paragraphs(pieces)


def via_subs(video_id, langs, auto):
    WORK_DIR.mkdir(exist_ok=True)
    for lang in langs:
        for old in WORK_DIR.glob(f"{video_id}.sub.*"):
            old.unlink()
        ytdlp(["--skip-download", "--write-auto-subs" if auto else "--write-subs",
               "--sub-langs", lang, "--sub-format", "vtt/srt/best",
               "-o", str(WORK_DIR / f"{video_id}.sub.%(ext)s"), watch_url(video_id)])
        files = sorted(WORK_DIR.glob(f"{video_id}.sub.*"))
        if files:
            try:
                return clean_vtt(files[0].read_text(encoding="utf-8", errors="replace"))
            finally:
                for f in files:
                    f.unlink()
    raise RuntimeError("nenhuma legenda em " + ", ".join(langs))


METHODS = {
    "whisper": ("mlx-whisper", via_whisper),
    "manual_subs": ("legenda manual do YouTube", lambda v: via_subs(v, TR["manual_sub_langs"], auto=False)),
    "auto_subs": ("legenda automática do YouTube", lambda v: via_subs(v, TR["auto_sub_langs"], auto=True)),
}


def transcribe(video_id, order=None):
    """Tenta os métodos em ordem. Devolve (caminho do .txt, método usado)."""
    errors = []
    for key in order or TR["order"]:
        label, fn = METHODS[key]
        try:
            text = fn(video_id)
        except Exception as e:
            log(f"Transcrição via {label} falhou: {e}")
            errors.append(f"{label}: {e}")
            continue
        words = len(text.split())
        if words < TR["min_words"]:
            log(f"Transcrição via {label} veio curta demais ({words} palavras); tentando o próximo método")
            errors.append(f"{label}: só {words} palavras")
            continue
        out = WORK_DIR / f"{video_id}.txt"
        out.write_text(text + "\n", encoding="utf-8")
        log(f"Transcrição via {label}: {words} palavras -> {out.name}")
        return out, label
    raise RuntimeError("nenhum método de transcrição funcionou (" + "; ".join(errors) + ")")


def video_id_from(arg):
    m = re.search(r"(?:v=|youtu\.be/|/shorts/|/live/)([\w-]{11})", arg)
    return m.group(1) if m else arg


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        sys.exit(__doc__)
    order = [args[args.index("--method") + 1]] if "--method" in args else None
    path, method = transcribe(video_id_from(args[0]), order)
    print(path)
