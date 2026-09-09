# Corrections de K Pro 6

## Composants intégrés

| Composant | Rôle |
|---|---|
| FI | Récolte locale de secours avant dégradation, avec garde de capacité |
| FJ2 | Réaffectation des plantations ne pouvant commencer avant l’échéance |
| FK | Fertilisation locale d’une tâche existante lorsque les conditions le permettent |
| FL | Comptabilité du blé après les actions des unités et les ventes réservées |
| FM | Réserve alimentaire alignée sur les nourrissages prévus |
| FN | Fichier autonome et point d’entrée explicite |

Ces composants conservent les corrections logistiques de K Pro 4.
La fertilisation anticipée généralisée et l’ouverture du quatrième quadrant
ne sont pas activées par ce regroupement.

## Recherche suivante

`research/pro6-next/care_horizon_fp.py` corrige expérimentalement l’échéance
d’utilité des soins. Le moteur consomme le bonus accumulé lors de la production
nocturne, puis ajoute le soin du jour au bonus suivant. Un soin ne doit donc pas
être valorisé comme s’il contribuait immédiatement à cette production.

Ce composant n’est **pas intégré au fichier K Pro 6 livré**. Son audit complet
et celui de ses interactions restent à poursuivre. Aucune nouvelle version
autonome n’est créée par cette archive.
