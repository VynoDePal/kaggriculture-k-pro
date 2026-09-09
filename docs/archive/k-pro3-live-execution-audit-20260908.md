> Archive technique éditée pour cette publication. Ce document n’est pas un rapport de performance ni un statut actuel de livraison.

## Périmètre et méthode

Par runtime : 0 divergence, 0 exception, 0 mutation parmi les 4 314 appels comparés. Les 12 contrôles de reset réussissent chacun sur l'action, l'état complet et la nonmutation de l'observation. Les 3 595 observations du siège 1 omettent `step` ; les 3 595 valeurs `last_step` sont exactement `day * 24 + hour`. Le fallback et les resets présents aux lignes 808, 834–836 sont ainsi exercés sur les données réelles.

## Preuves conservées

Aucun fichier source, outil ou configuration existant n'a été modifié par cet audit. Seuls ce rapport et les trois nouveaux fichiers d'audit ont été ajoutés.
