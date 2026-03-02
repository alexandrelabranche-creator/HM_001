---
name: doppelvelt-heatmap
description: >
  Workflow pour améliorer l’app Streamlit de heatmap (Rothmorgil) : UI, rendu, states,
  exports, conventions (0..6) et validation manuelle.
---

# Skill: Doppelvelt Heatmap (Rothmorgil)

## Scope
Cette skill sert à:
- ajouter/améliorer des features UI (filtres, régions, presets, undo/redo, click-to-edit sur carte),
- améliorer le rendu (sigma, alpha_min/max, gamma, alpha_gamma),
- préserver le format `state/state.json` et la rétrocompatibilité.

## Project layout
- App: `app/app.py`
- Rendu: `app/heatmap_render_lib.py`
- Carte: `assets/MAP.jpg`
- State: `state/state.json`
- Sorties: `outputs_heatmap/`

## Non‑negotiables
- `levels` : entiers 0..6.
- Ne pas ajouter d’alias dans `levels`.
- Toute option de rendu nouvelle doit être dans `render_standard` (avec défaut).
- Garder l’app lançable via `streamlit run app/app.py`.

## How to work
1) Lire AGENTS.md (règles et backlog).
2) Proposer un plan court.
3) Implémenter en petits commits/logiques.
4) Vérifier via exécution locale:
   - l’app démarre
   - preview change
   - export ok
   - save-to-state ok
   - bouton TPK ok

## Useful prompts
- “Utilise la skill $doppelvelt-heatmap. Ajoute un filtre ‘>0’ + recherche sur Ville.”
- “Ajoute un panneau de réglages de rendu (sigma/alpha/gamma/alpha_gamma) + presets.”
- “Ajoute un mode ‘cliquer la carte’ -> ville la plus proche -> slider.”
