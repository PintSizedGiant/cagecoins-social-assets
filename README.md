# cagecoins-social-assets

Public image hosting and build tools for Cage Coins social posts.

| Folder | What it holds |
|---|---|
| `posts/` | Rendered post images. Buffer and Airtable link to these files, so do not delete an image until its post has gone out. |
| `photos/` | Fighter cut-outs for the T7 card, one per fighter, named by ticker (for example `GANE.png`). PNG with a transparent background. |
| `tools/` | `query.sql` (read-only database query), `build.py` (turns the query result into cards and a manifest), `cc_render.py` (the templates), `fonts/`. |
| `test/` | Pipeline test images. |

Usage (daily plan, from 13/11/2026):

    python3 tools/plan.py raw.json --today YYYY-MM-DD --out build --photos-ok GANE,HOKI
    python3 tools/check_captions.py build/manifest.json captions.json
    python3 tools/record.py posted build/manifest.json "KEY|PLATFORM" ...
    python3 tools/record.py run YYYY-MM-DD done "summary"

`plan.py` picks the posts for the run (Half 1 review on Sundays, Half 2 preview on Wednesdays, filler in quiet weeks, monthly posts on the 1st), renders them and gives each a slot. `build.py` is the older per-set builder and still holds shared helpers.

| Also in the repo | What it holds |
|---|---|
| `config/blocked_usernames.txt` | Usernames shown as *** on leaderboard posts. Edit on GitHub. |
| `log/posted.jsonl` | One line per post scheduled. Used to skip duplicates and for the 14-day fighter cooldown. |
| `log/runs/` | One file per run day: done or failed, with reasons. Retries read this. |
| `snapshots/` | Leaderboard copy from each run. The 1st-of-month post uses the last one from the month before. |

Templates: T1 mover (text), T2 matchup, T3 recap carousel, T4 biggest movers, T5 prospect watch, T6 top trader, T7 fighter card (`tools/cc_fighter.py`, uses `photos/TICKER.png`), T8 Finish card for KO/TKO and submission wins and losses (`tools/cc_finish.py`), T9 head to head before the fight and T10 head to head result (`tools/cc_h2h.py`), T11 event card, T12 leaderboard, T13 big growers and the restyled T6 trader of the month (`tools/cc_extra.py`). Fighters without a cleared image get the no-photo stand-in (`tools/cc_fallback.py`). T7 to T10 use `photos/TICKER.png`. T1p (`t1p` in `cc_render.py`) is retired in favour of T7.

Fonts in `tools/fonts/`: Inter and Barlow Condensed (SIL Open Font License 1.1) and DejaVu Sans Mono (Bitstream Vera / DejaVu licence). Flags in `tools/flags/`: flag-icons (MIT). Licence files are in those folders.

T7 needs `pip install pillow cairosvg`.

Cage Coins is an independent fan game and is not affiliated with or endorsed by the UFC.
