> Archive technique éditée pour cette publication. Ce document n’est pas un rapport de performance ni un statut actuel de livraison.

## Identité des profils et intégrité

Les profils initiaux smoke-overflow et smoke-combined sont conservés comme résultats historiques, mais remplacés par r2 après la découverte séparée d'un cas limite d'exécution. Le fait que leurs 24 cellules terminent sans erreur ne valide pas ce cas limite. Les totaux identiques combined/all_safe dans ce smoke ne prouvent pas l'équivalence des versions. Ne pas promouvoir les anciens bytes sur la base de cette absence d'erreur.
