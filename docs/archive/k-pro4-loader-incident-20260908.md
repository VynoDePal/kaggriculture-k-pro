> Archive technique éditée pour cette publication. Ce document n’est pas un rapport de performance ni un statut actuel de livraison.

## Cause reproduite

Le chargeur installé `kaggle_environments.agent.get_last_callable` sélectionne la dernière valeur callable du module. L'empaquetage avait ajouté les helpers après `agent`, laissant `project_unit_phase` en dernière position. Appelé avec observation et configuration, ce helper renvoie une observation, pas les commandes `farmer`, `hands`, `market` attendues. Aucun traceback Python n'est nécessaire pour que le bot ne joue pas.

Les tests de stratégie et de parité précédents appelaient explicitement `module.agent` ; ils validaient la politique et le moteur, mais contournaient cette frontière de chargement. Le statut Kaggle COMPLETE ne validait pas le comportement. Il s'agit d'une erreur d'empaquetage et de couverture de validation, pas d'une faiblesse stratégique expliquant ces parties.

## Correction locale, sans nouvelle soumission

La recherche stratégique est suspendue pendant la résolution de cet incident. Aucun nouveau run stratégique ni nouvelle soumission n'est lancé après le signalement. Les candidats de recherche qui ajoutent des helpers après `agent` ne doivent jamais être envoyés tels quels : le contrôle du chargeur est obligatoire avant toute future soumission.
