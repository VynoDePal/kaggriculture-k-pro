> Archive technique éditée pour cette publication. Ce document n’est pas un rapport de performance ni un statut actuel de livraison.

## Ce qui a été reconstruit

Le plan économique choisit les effectifs, les cultures, les terrains et les
provisions. Il devient une liste de tâches par case. Une affectation globale
des ouvriers arbitre distances, urgences, zones et ressources disponibles.
Les ventes et achats sont ordonnés dans la limite des dix ordres du tour.
La fin de partie réserve le temps nécessaire au dépôt puis à la vente.

« Déterministe » ne signifie pas « script fixe » : à observation et mémoire
identiques, la décision est reproductible ; des marchés, stocks, récoltes ou
positions différents peuvent donner des décisions différentes.

Les deux partagent la même table d'actions ; Titan ajoute des conversions de lots
vaches/moutons. Les traiter comme deux familles indépendantes exagérerait la
diversité du test. Un troisième agent dynamique externe est ajouté au corpus.

## Mécaniques déterminantes vérifiées

Deux précisions utiles pour le diamant ont été vérifiées dans les deux moteurs :
les quatre cases du hangar autorisent déplacements, PICKUP et DROP même avec le
seul quadrant NW acheté. En revanche, construire une pâture dans une case encore
LOCKED échoue. Acheter le quadrant procure donc des droits de production, pas
l'accès logistique au hangar lui-même.

Exemple de spéculation au jour zéro : acheter 60 blés au stock marché initial
coûte 1 812, non 60 × 25. À marché autrement fixe, revendre 55 rapporte 1 679 ;
les cinq restants ont une valeur de liquidation de 133. Le prix affiché après
l'achat est en partie provoqué par cet achat : ce n'est pas un bénéfice gratuit.
Cela ne constitue pas un test exhaustif des stratégies de conservation plusieurs
jours ; aucune promesse de rendement n'en est tirée.

## Ce qui a réellement aidé, et ce qui a régressé

Les effets ci-dessous sont locaux aux snapshots et banques indiqués. Ils ne
s'additionnent pas automatiquement lorsqu'on combine les options.

### Compatibilité et coût d'exécution

Contrôles du fichier gelé déjà terminés : équivalence de 2 876 décisions avec le
prototype configuré, y compris tous les scores d'anticipation ; parité de
720 états dans chacun des deux sièges avec le moteur officiel ; deux parties
complètes via le chargeur officiel des fichiers, statuts DONE/DONE sans timeout.
La grammaire du fichier est compatible Python 3.10 ; les exécutions locales ont
été faites sous Python 3.14. Ses seuls imports sont `math` et `copy`.

Sur les 2 800 parties natives, la décision maximale mesurée est de **0,963 s**
murale ; le percentile 99 des maxima par partie est **0,750 s**. Ce ne sont pas
des mesures sur les serveurs Kaggle : le laboratoire natif ne fait pas appliquer
un timeout dur par décision. Les deux contrôles avec le chargeur officiel, eux,
se terminent sans timeout. La configuration officielle locale dispose de 1 s
par action et de 60 s de réserve cumulée. Son paquet est `kaggle-environments`
1.32.7 ; les empreintes des moteurs sont dans le contrôle de banque.
