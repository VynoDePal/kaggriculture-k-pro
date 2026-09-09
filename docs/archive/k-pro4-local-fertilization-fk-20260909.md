> Archive technique éditée pour cette publication. Ce document n’est pas un rapport de performance ni un statut actuel de livraison.

## Correction du risque laissé ouvert par FJ2

`local_fertilization_fk.py` s'installe après FJ2 sur une copie expérimentale du module de référence. Un ouvrier inactif portant de l'engrais peut accomplir une tâche FERTILIZE déjà proposée sur sa case, réservée à un autre ouvrier actuellement en déplacement. Les autres actions, y compris ce déplacement, restent intactes ; aucune réécriture de la mémoire des cibles. Les unités à action fixe et leurs cibles éventuellement anciennes sont exclues. La projection canonique doit montrer exactement une unité d'engrais consommée par cet ouvrier et l'effet sur cette plante, sans aucune autre différence d'état. Un second ouvrier ou une observation suivante où la plante est déjà fertilisée ne peut doubler le service.

## Tests et audits

Trois tests ont d'abord échoué sur FJ2 seul : service local absent, rendement4au lieu6 dans la situation contrôlée, absence de prise en charge par l'un de deux ouvriers inactifs. Ils passent avec FK. Un test rouge complémentaire détecte le cas d'une cible mémorisée appartenant à une unité à action fixe ; le garde-fou est ajouté. Dix tests FK couvrent également absence d'engrais/tâche, tâche déjà accomplie, action active, propriétaire non en déplacement, immutabilité, double service et observation du tour suivant.
