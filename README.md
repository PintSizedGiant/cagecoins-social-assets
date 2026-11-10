# cagecoins-social-assets

Public image hosting and build tools for Cage Coins social posts.

| Folder | What it holds |
|---|---|
| `posts/` | Rendered post images. Buffer and Airtable link to these files, so do not delete an image until its post has gone out. |
| `photos/` | Optional fighter cut-outs, one per fighter, named by ticker (for example `WLKR.png`). Transparent background works best. |
| `tools/` | `query.sql` (read-only database query), `build.py` (turns the query result into cards and a manifest), `cc_render.py` (the templates), `fonts/`. |
| `test/` | Pipeline test images. |

Usage:

    python3 tools/build.py raw.json --set recap preview midweek trader --out build --photos-ok WLKR,GANE

Templates: T1 mover (text), T1p mover (photo), T2 matchup, T3 recap carousel, T4 biggest movers, T5 prospect watch, T6 top trader.

Fonts in `tools/fonts/`: Inter (SIL Open Font License 1.1) and DejaVu Sans Mono (Bitstream Vera / DejaVu licence).

Cage Coins is an independent fan game and is not affiliated with or endorsed by the UFC.
