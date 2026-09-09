> Archive technique éditée pour cette publication. Ce document n’est pas un rapport de performance ni un statut actuel de livraison.

# Plan d'implémentation : affectation par tâche G

Objectif validé par l'utilisateur : remplacer l'exclusivité par case par une affectation de tâches compatible avec les ressources et l'ordre canonique. Exécution directe dans la worktree déterministe existante ; aucun fichier soumis ni capsule historique modifié.

## Architecture et limites de cette première étape

Cette première étape planifie le tour courant et vérifie la faisabilité du trajet jusqu'à l'échéance. Ce n'est ni un solveur optimal de toute la journée ni une nouvelle politique de marché. Les priorités restent des heuristiques héritées, pas un calcul exact du bénéfice.

## Fichiers et contrats

- `k_pro/pro5/prototype_tasks.py` : copie de K Pro 4 corrigé, nouvelle affectation ; point d'entrée Kaggle toujours dernier callable.
- `tests/test_k_pro5_task_planner.py` : appels réels à `act_units` et vérification de la phase projetée.
- `k_pro/pro5/candidate_task_planner_g.py` : fichier autonome figé seulement après tests.
- `docs/k-pro5-task-planner-g-report.md` : protocole avant résultats, preuves et décision.

Interface interne : `assign_unit_tasks(obs, st, work, actions, fixed)` renvoie la liste d'actions et actualise `st['targets']` pour les ouvriers non réservés. Les commandes de `fixed` sont conservées. La projection préfixe n'applique jamais une commande d'un ouvrier ultérieur.

## Étapes

Contraintes : CPU seulement, sources figées, graines de test non communiquées aux agents, deux sièges équilibrés, capsules/checkpoints canoniques sur DePal. Pas de nouvelle soumission Kaggle.
