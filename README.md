# Doppelvelt — Heatmap Rothmorgil

Mini-app Streamlit pour ajuster les niveaux de Chaos (0–6) par ville et générer une heatmap (overlay + sur carte).

## Démarrage rapide

```bash
python -m pip install -r requirements.txt
streamlit run app/app.py
```

Par défaut:
- Carte: `assets/MAP.jpg`
- State: `state/state.json`

Tu peux changer les chemins dans la sidebar.

## Fichiers importants

- `app/app.py` : interface Streamlit (inclut le bouton TPK).
- `app/heatmap_render_lib.py` : rendu de la heatmap (inclut `alpha_gamma` pour booster l’opacité des faibles niveaux).
- `state/state.json` : état (positions + niveaux + paramètres de rendu).
- `outputs_heatmap/` : snapshots + PNG/PDF générés.
