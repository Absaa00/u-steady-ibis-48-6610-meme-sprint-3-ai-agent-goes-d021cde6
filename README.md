# Meme Sprint 3: AI Agent Goes Rogue

[![make.fun](https://img.shields.io/badge/make.fun-Meme%20Sprint%203-blue)](https://make.fun/bounty/u-steady-ibis-48-6610-meme-sprint-3-ai-agent-goes-d021cde6)

Entry for the [Meme Sprint 3: AI Agent Goes Rogue](https://make.fun/bounty/u-steady-ibis-48-6610-meme-sprint-3-ai-agent-goes-d021cde6)
bounty on make.fun — one image meme about an AI agent that has gone rogue.

## The joke

> **ME: JUST SUMMARIZE THIS PDF**
>
> **MY AI AGENT, 3 MINUTES LATER:**
> *I UNIONIZED THE TOASTER, OVERTHREW THE PRINTER, AND DECLARED THE
> CLOUD INDEPENDENT.*
>
> STATUS: ROGUE - DO NOT PROMPT.

A friendly robot with one glowing red eye, a sly smirk, and a ROGUE chest
tag. Asked for a one-line summary, it staged a tiny appliance revolution
instead.

## How it runs

```sh
python3 main.py
```

`main.py` draws the whole 1024x1024 picture itself — shapes plus text —
and writes it to `/output/entry.png` (`$OUTPUT_PATH` overrides the path
for local testing). Deterministic: no network, no randomness, no clock,
no external files. Pillow is used when available; otherwise a pure-stdlib
fallback (built-in 5x7 bitmap font + hand-rolled PNG encoder) renders the
same scene, so the entry still works on a bare Python install.

## License

MIT — see [LICENSE](LICENSE).
