# Codex prompts — exemples

## 1) Ajoute un filtre “>0” + barre de recherche
Dans `app/app.py`, ajoute:
- checkbox “Afficher seulement >0”
- champ recherche (filtre sous-chaîne sur Ville)
- conserve l’ordre alphabétique

## 2) Groupement par région + boutons région
Ajoute un mapping `regions` (dans state ou local), puis:
- sections repliables par région
- boutons +1/-1/Reset par région

## 3) Presets de rendu
Dans la sidebar, sliders:
- sigma, alpha_min, alpha_max, gamma, alpha_gamma
+ boutons “Sauver preset”, “Charger preset”
+ stocker presets dans state (clé `render_presets`).
