# GIS Studiegebied Tool

Webapplicatie waarmee je een studiegebied op een kaart tekent (of opzoekt) en
daarbinnen automatisch relevante GIS-lagen van [PDOK](https://www.pdok.nl/)
laat downloaden, uitknippen op het gebied en bundelen in één zip-bestand.

## Hoe het werkt

1. In de frontend teken je een polygoon op de kaart of zoek je een locatie op.
2. Je selecteert welke PDOK-lagen (BAG, BGT, BRT TOP10NL, BRO, kadastrale
   grenzen, 3D-data, etc.) je nodig hebt.
3. De backend zet dit om in een achtergrondjob: lagen worden opgehaald bij
   PDOK, geknipt op het studiegebied en gereprojecteerd naar EPSG:28992.
4. Zodra de job klaar is kun je het resultaat downloaden als één zip.

## Projectstructuur

- `backend/` — Python/FastAPI-service die jobs aanmaakt, PDOK bevraagt,
  data knipt/reprojecteert en bundelt (`app/routers`, `app/services`,
  `app/jobs`, `app/layers_registry.py`).
- `frontend/` — Vite + OpenLayers webinterface om een studiegebied te
  tekenen/zoeken en lagen te selecteren.
- `data/` — lokale cache- en jobmappen (niet in git; gegenereerd tijdens
  gebruik).

## Backend draaien

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Frontend draaien

```bash
cd frontend
npm install
npm run dev
```

## Niet in git

- `.claude/` — lokale Claude Code-instellingen, niet relevant voor het
  project en bewust uitgesloten via `.gitignore`.
- `backend/.venv/`, `frontend/node_modules/`, `frontend/dist/` — installeer/
  build je lokaal opnieuw.
- `data/tmp_jobs/`, `data/cvgg_cache/`, `data/tile_cache/` — gegenereerde
  cache- en jobbestanden.
# Gis-studiegebied-tool
# Gis-studiegebied-tool
