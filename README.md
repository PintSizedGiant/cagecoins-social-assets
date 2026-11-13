# cagecoins-social-assets

Public image hosting and build tools for Cage Coins social posts.

| Folder | What it holds |
|---|---|
| `posts/` | Rendered post images. Buffer and Airtable link to these files, so do not delete an image until its post has gone out. |
| `photos/` | Fighter cut-outs for the T7 card, one per fighter, named by ticker (for example `GANE.png`). PNG with a transparent background. |
| `tools/` | `query.sql` (read-only database query), `build.py` (turns the query result into cards and a manifest), `cc_render.py` (the templates), `fonts/`. |
| `test/` | Pipeline test images. |

Usage:

    python3 tools/build.py raw.json --set recap preview midweek trader --out build --photos-ok WLKR,GANE

Templates: T1 mover (text), T2 matchup, T3 recap carousel, T4 biggest movers, T5 prospect watch, T6 top trader, T7 fighter card (`tools/cc_fighter.py`, uses `photos/TICKER.png`), T8 Finish card for KO/TKO and submission wins (`tools/cc_finish.py`, same image). T1p (`t1p` in `cc_render.py`) is retired in favour of T7.

Fonts in `tools/fonts/`: Inter and Barlow Condensed (SIL Open Font License 1.1) and DejaVu Sans Mono (Bitstream Vera / DejaVu licence). Flags in `tools/flags/`: flag-icons (MIT). Licence files are in those folders.

T7 needs `pip install pillow cairosvg`.

Cage Coins is an independent fan game and is not affiliated with or endorsed by the UFC.
