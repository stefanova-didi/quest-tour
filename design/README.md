# Quest City Tour — look & feel proposals

Four green visual directions for the player app, each tied to a real Sofia place or material.
Open `index.html` in a browser (no server needed).

**Applied to the app:** 02c Evening Domes · Cards (tokens in `frontend-mocks/ds/questcity/tokens.json`, styles in `frontend/src/styles/`, fonts in `frontend/src/fonts/`).

- `index.html` — overview, side-by-side table, how to review
- `00-baseline.html` … `03-vitosha.html` — one page per direction: palette, type specimen, five phone screens, notes
- `00b…00d-*.html`, `02b…02d-*.html` — variants of 00 and 02 (components, fonts, highlights, icon style); each loads its parent theme first
- `themes/NN-slug.css` — the tokens and motif rules of each direction (edit and reload)
- `base.css` — shared screen structure; token names match the app's `tokens.json`
- `build.py` — regenerates the six pages from one shared screen template (`python3 build.py`)
- `img/` — the original mock illustrations, kept for reference (the pages use inline SVG that recolours per theme)

- `fonts/` — self-hosted woff2 files and `fonts.css` (all SIL OFL); regenerate with `python3 fetch-fonts.py`

The pages work fully offline.
