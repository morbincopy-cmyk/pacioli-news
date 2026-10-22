"""Resumo da transcrição com `claude -p` (via summarize.sh).

Transcrições longas são divididas em partes: cada parte vira anotações
(prompts/parte.md) e as anotações são consolidadas com prompts/resumo.md.

Uso isolado:
    python3 pipeline/summary.py <video_id> "<título do vídeo>"
"""
import os
import re
import sys

from common import CONFIG, PROMPTS_DIR, ROOT, WORK_DIR, log, run

SUMMARIZE_SH = ROOT / "pipeline" / "summarize.sh"
SM = CONFIG["summary"]
CLAUDE_TIMEOUT = 900


def call_claude(prompt, text):
    """Uma chamada ao summarize.sh. Devolve a resposta (pode vir vazia)."""
    prompt_file = WORK_DIR / "prompt.tmp.md"
    prompt_file.write_text(prompt, encoding="utf-8")
    try:
        env = dict(os.environ, CLAUDE_BIN=CONFIG["paths"]["claude"])
        r = run([str(SUMMARIZE_SH), str(prompt_file)], timeout=CLAUDE_TIMEOUT, input=text, env=env)
    finally:
        prompt_file.unlink(missing_ok=True)
    if r.returncode != 0:
        err = (r.stderr or r.stdout or "").strip().splitlines()
        raise RuntimeError("claude -p falhou: " + (err[-1] if err else f"código {r.returncode}"))
    return r.stdout.strip()


def split_chunks(text, limit):
    """Divide nos limites de parágrafo, cada parte com até `limit` caracteres."""
    chunks, current = [], ""
    for para in text.split("\n\n"):
        if current and len(current) + len(para) + 2 > limit:
            chunks.append(current)
            current = ""
        current = f"{current}\n\n{para}" if current else para
    if current:
        chunks.append(current)
    return chunks


def normalize(output, title):
    """Valida a saída e devolve o Markdown com o título exato do vídeo.

    Tem que começar com um título '## ' e trazer a seção 'Em uma frase'.
    """
    text = output.strip()
    text = re.sub(r"^```(?:markdown|md)?\s*\n(.*)\n```$", r"\1", text, flags=re.S).strip()
    if not text:
        raise ValueError("resposta vazia")
    first, _, rest = text.partition("\n")
    if not first.startswith("## "):
        raise ValueError(f"não começa com o título esperado (veio: {first[:80]!r})")
    if "Em uma frase" not in rest:
        raise ValueError("falta a seção 'Em uma frase'")
    return f"## {title}\n{rest.rstrip()}\n"


def summarize_once(text, title, chunk_chars):
    base_prompt = (PROMPTS_DIR / "resumo.md").read_text(encoding="utf-8").strip()
    final_prompt = f"{base_prompt}\n\nTítulo do vídeo: {title}"

    if len(text) <= chunk_chars:
        return call_claude(final_prompt, text)

    chunks = split_chunks(text, chunk_chars)
    log(f"Transcrição longa ({len(text)} caracteres): resumindo em {len(chunks)} partes")
    part_prompt = (PROMPTS_DIR / "parte.md").read_text(encoding="utf-8").strip()
    notes = []
    for i, chunk in enumerate(chunks, 1):
        note = call_claude(f"{part_prompt}\n\nTítulo do vídeo: {title}\nEsta é a parte {i} de {len(chunks)}.", chunk)
        if not note:
            raise ValueError(f"anotações vazias na parte {i}")
        notes.append(f"### Parte {i} de {len(chunks)}\n\n{note}")
    combined = ("Observação: o vídeo era longo, então a transcrição foi dividida em partes "
                "e você vai receber as anotações detalhadas de cada parte, em ordem, "
                "em vez da transcrição completa.\n\n" + "\n\n".join(notes))
    return call_claude(final_prompt, combined)


def summarize(transcript_path, title, chunk_chars=None):
    """Gera o resumo validado. Tenta `summary.attempts` vezes; se todas falharem, levanta erro."""
    text = transcript_path.read_text(encoding="utf-8").strip()
    chunk_chars = chunk_chars or SM["chunk_chars"]
    last_error = None
    for attempt in range(1, SM["attempts"] + 1):
        try:
            result = normalize(summarize_once(text, title, chunk_chars), title)
            log(f"Resumo gerado ({len(result.split())} palavras, tentativa {attempt})")
            return result
        except Exception as e:
            last_error = e
            log(f"Resumo falhou na tentativa {attempt}: {e}")
            if "authenticate" in str(e).lower():
                break  # sessão expirada: tentar de novo agora não adianta
    raise RuntimeError(f"resumo falhou após {SM['attempts']} tentativas: {last_error}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    vid, title = sys.argv[1], sys.argv[2]
    chunk = int(sys.argv[3]) if len(sys.argv) > 3 else None
    md = summarize(WORK_DIR / f"{vid}.txt", title, chunk)
    out = WORK_DIR / f"{vid}.summary.md"
    out.write_text(md, encoding="utf-8")
    print(md)
