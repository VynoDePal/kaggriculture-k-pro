> Archive technique éditée pour cette publication. Ce document n’est pas un rapport de performance ni un statut actuel de livraison.

## K Pro 2 — candidat d'équilibrage, sans promotion

La géométrie autorise au plus trois quadrants avec un rayon diamant de six : ce n'est
pas une macro diamant 4Q complète. Les snapshots `pro2/` sont des expériences,
**pas une collection d'agents tous validés à soumettre**.

Pour vérifier la capsule, les dépendances et tous les checkpoints du test final
de K Pro 2 **sans exécuter de partie**, depuis cette worktree et avec le disque
externe monté :

## Architecture

L'agent lit l'observation publique et ses propres stocks. Il construit un plan de
capital, de troupeau et de cultures, crée les tâches nécessaires pour chaque case,
affecte les ouvriers sans conflit, organise leur ravitaillement puis les ventes.
Les stocks portés ne sont jamais confondus avec de l'argent déjà gagné.

## Vérifications reproductibles

Depuis cette worktree, les tests du périmètre sont :

Pour vérifier à nouveau la campagne finale déjà terminée, en conservant son
répertoire et son manifeste intacts :
