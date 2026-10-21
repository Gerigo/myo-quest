# MYO Quest — anatomie pour coach sportif

Application française d’étude du mouvement et de révision sur un corps 3D.

## Démarrer
Depuis ce dossier : `npm start`, puis ouvrir http://localhost:4173/.
Le site statique est entièrement contenu dans `dist/` : aucun build ni API nécessaire.
`npm test` vérifie le catalogue, la géométrie, la latéralité et les correspondances pédagogiques.

## Étudier
Cliquez sur un muscle : fonction en langage clair, origine et insertion visibles, exemple en salle et point à retenir. Les détails anatomiques et l’innervation restent accessibles.
116 fiches documentées ; 40 profils possèdent une explication spécifique orientée salle de sport. Les autres fiches proposent une reformulation et un cadre général d’analyse, sans inventer d’exercice spécifique.

## Réviser
- **Trouve ce muscle** : un nom, puis sélection sur le corps.
- **Quel muscle fait ça ?** : une fonction et un repère discriminant, puis sélection.
- 5 questions par série ; choix Essentiels coach ou région ; gauche et droite acceptés.
- Indice, correction visuelle, XP, niveaux et progression locale.

## Naviguer
Glisser pour tourner ; choisir **Déplacer** pour glisser librement verticalement et horizontalement. Molette pour zoomer, double-clic pour cadrer. Maj + glisser / clic droit et flèches au clavier permettent également le déplacement. Les vues Main et Pied ciblent le côté gauche ; les boutons de côté de la fiche permettent de changer de côté. Recherche sans répétition bilatérale, masquage et isolation.

## Modèle et précision
744 structures : 462 musculaires, 210 osseuses, 31 cartilagineuses, 28 dentaires et 13 tendineuses. Ce sont des structures de maillage, pas un décompte canonique des muscles ou des os du corps.
2 508 461 triangles issus des maillages de base Z-Anatomy / BodyParts3D, sans décimation. Deux GLB d’environ 61 Mo au total. Le modèle est plus lourd que la première version ; le rendu est à la demande hors animation de sélection.
Les groupes présents dans la source restent groupés ; toutes les structures n’ont pas encore de fiche. Elles sont alors exclues des défis. Les modificateurs Blender ne sont pas évalués : les cavités fines de l’ethmoïde demandent notamment une amélioration ultérieure. Les insertions sont décrites textuellement et ne sont pas des empreintes 3D validées.
Revue technique et documentaire, **pas validation clinique par un anatomiste**, ni programme officiel d’une certification coach donnée.
Crédits et licence CC BY-SA 4.0 dans `dist/assets/ATTRIBUTION.txt` et `Z-Anatomy-LICENSE.txt`.

## Structure du code
- `dist/app.js` : parcours d’étude, défis et progression.
- `dist/viewer.js` : Three.js, caméra, picking, couches et halo.
- `dist/anatomy-data.js` : fiches anatomiques et références.
- `dist/coach-data.js` : reformulations et exemples pédagogiques.
- `dist/assets/atlas.json` : noms, catégories, provenance et correspondances.
- `scripts/` : conversion de la source et localisation. Exécution depuis le dossier parent du projet ; source attendue dans `work/source-anatomy/Z-Anatomy/Startup.blend`. Dépendances de conversion : Python, numpy, blender-asset-tracer. Exécuter `raw_inventory.py`, `export_raw_atlas.py`, puis `localize-atlas.mjs`. Les scripts ne lancent pas le code intégré au modèle.

La progression est conservée dans localStorage (`myo-quest-v1`). Il n’y a pas de compte ni de synchronisation distante.
