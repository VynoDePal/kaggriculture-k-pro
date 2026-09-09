> Archive technique éditée pour cette publication. Ce document n’est pas un rapport de performance ni un statut actuel de livraison.

# J — ventilation exploratoire des attentes

Analyse secondaire réalisée après le rapport principal, sur les mêmes 16 trajectoires conservées. Aucune partie ni politique nouvelle. Les comptes portent sur des observations d'ouvriers, pas sur autant de tâches indépendantes ou d'actions récupérables.

Parmi les 7 993 observations sans coût réel fini, **6 846 ont lieu entre 20 h et 23 h**. Cela suggère de vérifier les contraintes d'heure et de faisabilité, mais n'isole pas leur cause : le masque de coût intègre aussi déplacement, inventaire, action disponible et retour final. Les associations avec les inventaires vides ne prouvent pas qu'un achat ou un détour aurait aidé.

Le planificateur n'est donc pas simplement en train de laisser systématiquement une tâche libre et jugée faisable à côté d'un ouvrier PASS. Cela ne prouve pas que le plan de culture, les ressources ou la génération des tâches soient optimaux. Il faut agir plus en amont si l'on veut créer du travail utile.

Une piste distincte à vérifier dans l'historique avant toute nouvelle expérience est l'anticipation exacte des graines de remplacement des cultures récoltées. Le `market_orders` actuel calcule la demande sur les cases déjà EMPTY/WEED dans l'observation : une récolte du tour courant peut ne pas encore y être représentée. Une commande de graines ne peut toutefois pas financer une plantation dans la même phase d'actions ; il faudra vérifier un vrai préfixe atteignable et les ordres effectivement exécutés. Ce constat de code ne garantit aucun gain et ne justifie pas un stock tampon général.
