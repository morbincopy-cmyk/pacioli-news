"""Agendamento no launchd, gerado a partir de config.json (schedule.start_hour..end_hour).

    python3 pipeline/schedule.py install   # gera o plist e (re)carrega o agendamento
    python3 pipeline/schedule.py pause     # descarrega (para de rodar), mantém o plist
    python3 pipeline/schedule.py resume    # carrega de novo
    python3 pipeline/schedule.py run       # dispara agora pelo launchd (kickstart)
    python3 pipeline/schedule.py status
"""
import os
import plistlib
import subprocess
import sys
from pathlib import Path

from common import CONFIG, ROOT

LABEL = "com.bernardo.pacioli-news"
PLIST = Path.home() / "Library" / "LaunchAgents" / f"{LABEL}.plist"
DOMAIN = f"gui/{os.getuid()}"


def build_plist():
    sched = CONFIG["schedule"]
    hours = range(sched["start_hour"], sched["end_hour"] + 1)
    return {
        "Label": LABEL,
        "ProgramArguments": ["/bin/bash", str(ROOT / "run.sh")],
        "WorkingDirectory": str(ROOT),
        # Uma entrada por hora cheia. Se o Mac estiver dormindo, o launchd roda
        # a execução perdida quando ele acordar (o cron simplesmente pularia).
        "StartCalendarInterval": [{"Hour": h, "Minute": 0} for h in hours],
        "StandardOutPath": str(ROOT / "logs" / "launchd.out.log"),
        "StandardErrorPath": str(ROOT / "logs" / "launchd.err.log"),
        "ProcessType": "Background",
        "RunAtLoad": False,
    }


def launchctl(*args, check=False):
    r = subprocess.run(["/bin/launchctl", *args], capture_output=True, text=True)
    if check and r.returncode != 0:
        sys.exit(f"launchctl {' '.join(args)} falhou: {(r.stderr or r.stdout).strip()}")
    return r


def unload():
    launchctl("bootout", f"{DOMAIN}/{LABEL}")


def load():
    launchctl("bootstrap", DOMAIN, str(PLIST), check=True)


def main(cmd):
    if cmd == "install":
        (ROOT / "logs").mkdir(exist_ok=True)
        PLIST.parent.mkdir(parents=True, exist_ok=True)
        with open(PLIST, "wb") as f:
            plistlib.dump(build_plist(), f)
        unload()
        load()
        s = CONFIG["schedule"]
        print(f"Agendado: de hora em hora, das {s['start_hour']}h às {s['end_hour']}h ({PLIST})")
    elif cmd == "pause":
        unload()
        print("Agendamento pausado.")
    elif cmd == "resume":
        load()
        print("Agendamento reativado.")
    elif cmd == "run":
        launchctl("kickstart", f"{DOMAIN}/{LABEL}", check=True)
        print("Execução disparada; acompanhe em logs/.")
    elif cmd == "status":
        r = launchctl("print", f"{DOMAIN}/{LABEL}")
        if r.returncode != 0:
            print("Não carregado (pausado ou não instalado).")
        else:
            keep = ("state =", "last exit code", "runs =")
            print("\n".join(l.strip() for l in r.stdout.splitlines() if l.strip().startswith(keep)))
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "")
