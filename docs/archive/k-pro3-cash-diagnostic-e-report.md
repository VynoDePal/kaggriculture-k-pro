> Archive technique éditée pour cette publication. Ce document n’est pas un rapport de performance ni un statut actuel de livraison.

## Ce que la vache change réellement dans ce petit diagnostic

Pour J6, première vache achetée et posée à J5, première vente de lait à J14. Pour vache-J6, acquisition/pose à J0 et première vente à J8 dans les12 trajectoires. Le mécanisme de revenu plus précoce fonctionne ici.

## Couplage aléatoire confirmé, pas une nouvelle découverte revendiquée

Le moteur officiel réinitialise un RNG pour chaque jour, puis tire les mauvaises herbes sur les seules cases vides, puis un commerce dans le même RNG. Modifier l'occupation du sol peut donc modifier le commerce tiré. Ce mécanisme était déjà documenté dans `docs/phase4-ralph-log.md:230` ; il est vérifié dans le moteur utilisé ici, `_spawn_weeds` et `_end_of_day`, lignes836–891.
