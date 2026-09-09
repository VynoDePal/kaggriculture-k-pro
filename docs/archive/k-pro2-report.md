> Archive technique éditée pour cette publication. Ce document n’est pas un rapport de performance ni un statut actuel de livraison.

### Arbitrage marginal

À partir du jour 6, la valeur d'une tâche mélange à parts égales l'ancienne
estimation et une estimation du gain marginal du bouquet d'actions proposé.
Elle distingue notamment récolte disponible, croissance par arrosage, coût de
fertilisation, nourriture et entretien des animaux. C'est une approximation,
pas un calcul exact de profit futur. Les urgences de survie sont prises en compte
mais cela ne garantit pas qu'aucune culture ou aucun animal ne sera perdu.

Dans l'affectation des ouvriers, diviser l'urgence par 500 au lieu de 250 redonne
plus de poids au trajet. Les zones, les contrôles de légalité et les règles de
fin de partie restent ceux de la base. L'anticipation locale coûteuse est désactivée
dans ce profil : sa vitesse ne doit pas être présentée comme une optimisation
à stratégie inchangée par rapport à K Pro 1.

## Exactitude, vitesse et limites

Ces contrôles utilisent la version locale installée de `kaggle-environments`
1.32.7 sous Python 3.14, pas une soumission au serveur de compétition. « Sans erreur » désigne
l'absence d'exception enregistrée par le runner ; cela ne prouve pas que chaque
action est utile ou que tous les déplacements sont optimaux.

Les appels d'anticipation atteignent environ 0,55 seconde CPU dans les contrôles
réalisés. Sous charge, le temps mural peut dépasser une seconde ; aucune garantie
de temps sur le matériel Kaggle n'est fournie. L'agent livré utilise uniquement
la bibliothèque standard Python ; le simulateur C++ reste un outil du laboratoire.

La base autorise au plus trois quadrants et un rayon diamant 6 : **ce n'est pas une macro
diamant 4Q complète**. Le stockage officiel par défaut est 100, pas 200 ; le dépôt
automatique nocturne existe, mais pas après la dernière action du dernier jour.
