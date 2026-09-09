> Archive technique éditée pour cette publication. Ce document n’est pas un rapport de performance ni un statut actuel de livraison.

## Résultat principal

Sur 106 212 commandes ouvrières, 18 082 sont PASS, réparties sur 3 455 décisions et les 16 jeux.

Les décisions des catégories peuvent se recouper ; leurs comptes ne s'additionnent pas pour obtenir les 3 455 décisions uniques.

Pour les 17 952 affectations fictives, le contrôle indépendant des matrices trouve **zéro colonne de culture non attribuée à coût fini pour l'ouvrier concerné**, même en incluant les tâches WATER/HARVEST sans PLANT. Ce constat porte sur les tâches et contraintes du planificateur actuel, pas sur toutes les actions légales possibles du jeu. Les 147 413 occurrences de colonnes de culture non attribuées à coût fini pour au moins un ouvrier peuvent concerner des ouvriers déjà occupés ; elles ne prouvent pas une possibilité pour un ouvrier PASS et ne sont pas autant de tâches distinctes.

## Conséquences pour la suite

Ne pas ajouter de pénalité générale PASS ni de remplacement opportuniste aveugle : le diagnostic ne trouve pas de travail de culture libre jugé réalisable pour ces ouvriers par la matrice actuelle. La coordination des graines est une piste précise mais minoritaire ; une éventuelle intervention devra vérifier qu'elle change réellement une décision utile, sans déplacer les pertes vers d'autres services. Aucun correctif de politique n'est activé par ce rapport.

La prochaine analyse peut séparer, dans les relevés déjà conservés, les ouvriers n'ayant aucune tâche réelle à coût fini de ceux qui ne peuvent servir que des tâches déjà attribuées, puis examiner les heures et les ressources correspondantes. C'est une analyse secondaire exploratoire, pas un gain établi. Toute nouvelle politique exigera pré-déclaration, préfixe identique et nouvelle banque commune ; J ne devient pas une banque de confirmation.

## Provenance et limites de validation

La revue initiale a corrigé un historique cumulatif incorrect et une détection limitée aux séquences PLANT. Les deux anciens diagnostics de développement restent intacts ; un contrôle hors simulation a reconstruit leurs 1 438 relevés via la fonction corrigée. Les nouvelles 16 trajectoires apportent la validation en exécution du relevé corrigé. Le rapport de préparation reconnaît que son premier échec de test était uniquement un import manquant, pas un vrai test comportemental rouge ; les régressions comportementales ont été ajoutées et observées avant les corrections, sans réécrire cette chronologie.
