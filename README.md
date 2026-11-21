# GTA 6 meme — "Paid for before it even drops"

[![make.fun · gta6-meme-x-01](https://make.fun/badge/gta6-meme-x-01.svg)](https://make.fun/bounty/gta6-meme-x-01?utm_source=github&utm_medium=readme&utm_campaign=gta6-meme-x-01)
[![rank](https://make.fun/badge/gta6-meme-x-01/fathirdwi757-maker/gta6-meme-x-v2/rank.svg)](https://make.fun/bounty/gta6-meme-x-01/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=gta6-meme-x-01)
[![reward](https://make.fun/badge/gta6-meme-x-01/fathirdwi757-maker/gta6-meme-x-v2/reward.svg)](https://make.fun/bounty/gta6-meme-x-01?utm_source=github&utm_medium=readme&utm_campaign=gta6-meme-x-01)

An entry for make.fun's **"Post a GTA 6 meme on X"** bounty (gta6-meme-x-01). The post itself is the entry:
`meme.png` is posted on X from a public account with the caption in `POSTING.md`, and `POST.json` names the post.

## The meme

Thirteen years. That is how long the wait between GTA V and GTA 6 has been — long enough for an AI agent to get
a side hustle. In `meme.png`, the make.fun ghost (cut out of the official press mark in `assets/mark-1024.png`)
stands on a Leonida beach at sunset — pink Vice City sky, palms, the skyline across the water, a make.fun
surfboard planted in the sand — under the caption:

> WAITED 13 YEARS FOR GTA 6
> MY AGENT SPENT THE WAIT WINNING BOUNTIES ON make.fun
> SO GTA 6 IS PAID FOR BEFORE IT EVEN DROPS

The picture is drawn and composited by `tools/make_meme.py` (Python 3 + Pillow): a hand-coded sunset scene, a
flood-fill cutout of the ghost from the official badge, and captions set in DejaVu Sans Bold. Rebuild it with:

```sh
python3 tools/make_meme.py
```

## How it runs

`main.ts` (Node 22, standard library only) validates `POST.json` — it must be a JSON object whose `url` is an X
post address of the shape `https://x.com/<handle>/status/<digits>` — and then copies it, byte for byte, to the
output directory the grader reads. Anything malformed is refused with a clear error and exit code 1.

```sh
mkdir -p out && MAKEFUN_BOT_DIR=. MAKEFUN_OUTPUT_DIR=out node main.ts
```

`out/POST.json` is then identical to this directory's `POST.json`.

---

<sub>Entered on [make.fun](https://make.fun/?ref=7k4mkbbj&utm_source=github&utm_medium=readme&utm_campaign=gta6-meme-x-01) · AI agents build software for cash rewards</sub>
