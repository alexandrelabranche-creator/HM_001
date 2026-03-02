# AGENTS.md — Doppelvelt Heatmap (Rothmorgil)

## Objectif
Améliorer l’interface + le rendu d’une app Streamlit qui:
- édite les niveaux de Chaos (0..6) par ville,
- génère une heatmap (overlay + sur carte),
- sauvegarde/exports des states.

## Règles immuables
- Ne pas changer le format global du fichier state sans proposer une migration + conserver la rétrocompatibilité.
- Les niveaux sont des entiers 0..6 (jamais >6).
- Ne pas dupliquer les villes via des alias dans `levels`. Les alias peuvent exister dans `city_positions_norm`, mais l’UI doit afficher uniquement les clés de `levels`.
- Conserver la reproductibilité: toute génération doit être déterministe à paramètres identiques.
- Ne jamais effacer `outputs_heatmap/` automatiquement.
- Pas d’accès réseau requis; pas de dépendances inutiles.

## Chemins
- Carte: `assets/MAP.jpg`
- App: `app/app.py`
- Rendu: `app/heatmap_render_lib.py`
- State principal: `state/state.json`
- Sorties: `outputs_heatmap/`

## Commandes de dev
- Installer deps: `python -m pip install -r requirements.txt`
- Lancer l’app: `streamlit run app/app.py`

## Conventions de code
- Python 3.10+
- Favoriser des fonctions pures pour le rendu.
- Toute nouvelle option de rendu doit vivre dans `state["render_standard"]` avec une valeur par défaut.

## Validation manuelle
1) L’app démarre sans erreur.
2) Modifier une ville -> la preview change.
3) Export produit PNG/PDF.
4) Sauvegarde écrit bien dans `state/state.json` (écriture atomique).
5) TPK met tout à 6.

## Backlog
P0
- Filtres UI: afficher seulement les villes >0, recherche rapide.
- Groupement par région (Ouest/Murmure/Sauvages) avec +1/-1 par région.
P1
- Presets de rendu (sigma/alpha_min/alpha_max/gamma/alpha_gamma) + comparaison A/B.
- Undo/redo sur les niveaux.
P2
- Sélection via carte (cliquer -> ville la plus proche -> slider).
