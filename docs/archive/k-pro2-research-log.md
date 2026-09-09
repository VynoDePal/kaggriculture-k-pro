> Archive technique éditée pour cette publication. Ce document n’est pas un rapport de performance ni un statut actuel de livraison.

## Objectif et méthode

CPU seulement, pools bornés selon RAM disponible. Artefacts volumineux sur DePal.
La recherche vise un meilleur agent sans promesse d'invincibilité.

## Deuxième vague — 20:49 UTC

Ouvertures B/12 et comptabilité différée D/12 terminées. Les ouvertures à dix
melons ou plus régressent fortement ; le mélange trois moutons/une vache n'est
pas meilleur. Ni l'activation comptable après l'ouverture, ni ses buffers de
nourriture n'améliorent le contrôle. Ces options restent désactivées.

## Troisième vague — 21:00 UTC

Pistes structurelles préparées :

- G : lots de provisions coordonnés, spécialistes après ouverture et dépôt
  groupé sans blé ni animaux transportés.
- H : suivre l'ordre d'une tournée construite par insertion, et non seulement
  utiliser cette tournée pour attribuer une zone.
- I : réserver une partie de la trésorerie au prochain terrain avant d'acheter
  de nouveaux animaux. Une ouverture2moutons/2vaches/12melons remplit bien les
  cases au jour1, mais sa croissance manque ensuite de trésorerie ; ce n'est
  pas un défaut de plantation initiale.
- J : valoriser le CARE avec un horizon économique, terminer un service avant
  la livraison, et espacer les ventes centrales quand la trésorerie est suffisante.

Contrôles supplémentaires :

## Quatrième vague — 21:23 UTC

65tests K Pro passent, dont les tests nouveaux du compilateur : rejet des clés
inconnues, des modifications tactiques non auditées et des accès CFG bruts.
Le compilateur original et K Pro1 restent inchangés. La variante finalement
retenue devra repasser l'équivalence de compilation avec ses propres paramètres.

## Confirmation et dernier test d'arbitrage — 21:32 UTC

La suite de tests a été exécutée avec pytest afin d'inclure aussi les fonctions
de test historiques non collectées par unittest :81tests passent à21:32UTC.
Les tests synthétiques du comparateur ne sont jamais comptés comme des parties.

## Résultats complets E initial et calcul conditionnel — 21:55 UTC

La partition système a atteint273Mo libres ; les résultats restaient sur DePal.
Après signalement, l'utilisateur a libéré de l'espace :2,9Go à21:52UTC.
Les bases et l'historique actifs de Codex n'ont pas été touchés.

## Intégration et garde-fous — 22:18 UTC

Vingt-et-un manifestes d'expérimentation et vingt-sept sources distinctes
sont revérifiés sans différence. Le compilateur et les outils d'audit sont
nouveaux ; ni K Pro1 ni les runners déjà verrouillés n'ont été modifiés.

## Sélection E et réaffectation CPU — 22:42 UTC

Les contrôles de l'arbitrage marginal passent : chargeur officiel sur deux
sièges, reset et déterminisme, entrée non mutée,24changements sur70sondes
synthétiques. La rotation conditionnelle conserve4 314actions et scores internes
sur six contrôles élargis ; les deux sièges passent720états de parité officielle.

Le disque système est de nouveau descendu à1,2Go à22:45UTC ; l'utilisateur
a confirmé libérer davantage d'espace. Il remonte à2,7Go puis reste à2,6Go
à23:02UTC. Les données de Codex et des autres projets n'ont pas été modifiées.

## Clôture des matrices finales — 23:45 UTC

Les trajectoires montrent moins de déplacements (2 930 → 2 606 par partie),
mais plus de PASS (946 → 1 224), plus de débordements (4,34 → 6,34 unités) et un
score propre moyen inférieur (97 946 → 90 624). Ces différences ne sont pas des
preuves causales : les comptages n'indiquent pas à eux seuls qu'un PASS était
évitable ni quelle action aurait été rentable.

La clôture recommande : stabilité arithmétique portable, moment d'activation de
l'urgence, arbitrage conditionnel public, interaction avec l'anticipation et
valorisation économique des actions disponibles. Aucun réglage n'est fait sur
la banque finale. Aucune promotion, remplacement ni soumission Kaggle.
