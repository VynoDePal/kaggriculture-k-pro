# Architecture K Pro

## Décision

Le plan de ferme détermine les besoins en cultures, animaux, terrains et ouvriers.
Chaque case produit une séquence de tâches : préparation, plantation, arrosage,
soins, récolte et collecte d’engrais. L’affectation tient compte de la distance,
des stocks portés, des zones de travail et des échéances journalières.

Les trajets et les ressources doivent être réalisables conjointement. Un revenu
potentiel ne peut financer un achat tant qu’une livraison et une vente ne sont
pas réellement possibles. Les stocks du hangar et ceux des ouvriers sont
comptabilisés séparément avant projection des actions.

## Intégration

K Pro 6 incorpore ses composants dans des espaces de noms distincts afin de
préserver les variables globales et l’ordre des adaptations. Son point d’entrée
est placé après les fonctions auxiliaires. Le fichier autonome ne dépend pas
des modules de laboratoire présents sur le poste de développement.

Les prototypes de `research/` explorent les calendriers de production, les
réservations partagées, le financement et la sélection de projets compatibles.
Ces composants ne sont pas automatiquement activés dans les versions livrées.

## Limites actuelles

- Coordonner plus efficacement les premières récoltes, l’élevage et les livraisons.
- Dimensionner les investissements selon le travail effectivement disponible.
- Améliorer le renouvellement des cultures et l’autonomie alimentaire.
- Développer une expansion productive vers quatre quadrants.
- Vérifier les interactions entre corrections, sans confondre un effet mécanique
  local avec une amélioration globale de la politique.
