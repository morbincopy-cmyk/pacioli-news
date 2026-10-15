"""Utilidades compartilhadas: caminhos, configuração, estado e log."""
import datetime as dt
import json
import os
import subprocess
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
CONFIG = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
TZ = ZoneInfo(CONFIG["timezone"])

STATE_FILE = ROOT / "state" / "processed.json"
SUMMARIES_DIR = ROOT / "state" / "summaries"
WORK_DIR = ROOT / "work"
SITE_DIR = ROOT / "site"
POSTS_DIR = SITE_DIR / "posts"
PROMPTS_DIR = ROOT / "pipeline" / "prompts"

YT_DLP = CONFIG["paths"]["yt_dlp"]


def now():
    return dt.datetime.now(TZ)


def log(msg):
    print(f"[{now():%H:%M:%S}] {msg}", flush=True)


def watch_url(video_id):
    return f"https://www.youtube.com/watch?v={video_id}"


def local_dt(timestamp):
    return dt.datetime.fromtimestamp(timestamp, TZ)


def load_state():
    """Retorna o estado salvo, ou None na primeira execução."""
    if not STATE_FILE.exists():
        return None
    return json.loads(STATE_FILE.read_text(encoding="utf-8"))


def empty_state():
    return {"processed": {}, "pending": {}}


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def save_state(state):
    write_json(STATE_FILE, state)


def run(cmd, timeout=600, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, **kw)


def ytdlp(args, timeout=600):
    r = run([YT_DLP, "--no-warnings", *args], timeout=timeout)
    if r.returncode != 0:
        err = (r.stderr or "").strip().splitlines()
        raise RuntimeError("yt-dlp falhou: " + (err[-1] if err else f"código {r.returncode}"))
    return r.stdout


def fail(msg):
    log("ERRO: " + msg)
    sys.exit(1)
