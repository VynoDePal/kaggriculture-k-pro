> Archive technique éditée pour cette publication. Ce document n’est pas un rapport de performance ni un statut actuel de livraison.

## Avancée de cette étape

Les corrections locales FI/FJ2/FK/FL/FM étaient validées sous forme de modules de laboratoire. Elles sont désormais réunies dans **un fichier Python autonome expérimental**, sans dépendance aux fichiers du dépôt ou du disque externe pendant ses décisions.

Ce chantier corrige le risque d'une intégration incomplète ou d'un mauvais point d'entrée. Il n'ajoute pas une nouvelle stratégie et ne prouve pas une amélioration du score. Aucun remplacement de référence, promotion ou soumission Kaggle.

## Bilan explicite des problèmes corrigés localement

Les correctifs de transport et de placement déjà présents dans K Pro 4 sont conservés. La fertilisation anticipée des melons reste non activée : elle consomme une ressource dont la compensation économique n'a pas été démontrée. Le quatrième quadrant reste désactivé dans cette référence ; ce fichier n'est donc pas un diamant4Q résolu.

## Construction contrôlée

`compile_local_fn.py` lit une seule fois les six sources nécessaires : référence, FJ2, FK, FL, FM, FI. Il refuse un membre manquant ou une empreinte différente. L'ordre d'installation est FJ2 → FK → FL → FM, puis FI comme enveloppe externe.

Le dernier callable est `kaggle_agent`, après tous les helpers. La compilation est reproductible ; le fichier et son manifeste sont créés exclusivement. Un fichier ou manifeste préexistant est préservé et provoque un refus. Les sources expérimentales déjà figées et les anciennes preuves restent intactes.

## Vérifications

Trois tests rouges initiaux sur le véritable chargeur Kaggle ont montré qu'une source neutre n'incluait pas FL, FM et FI. Après construction : ces comportements sont présents. Les tests complémentaires couvrent autonomie sans fichiers ni imports non standard, empreintes et reproductibilité, refus d'écrasement, indépendance des sièges et remise à zéro sur le début d'une nouvelle séquence enregistrée.

Mesures locales, sans tests concurrents pendant cet audit :

## État externe et sécurité

L'espace système était descendu à385Mo ; les caches contrôlés étaient trop petits pour une récupération utile. Aucune suppression effectuée. Dernier relevé :1,6Go libres système,121Go surDePal. Ne pas attribuer cette remontée à un nettoyage de l'agent. Tous les processus lancés dans cette étape sont terminés.

## Problèmes encore ouverts et suite

La relecture historique a retrouvé le rejet du recalcul global de priorité par ressources accessibles (`prototype_b/candidate_feasible`). Cette ancienne variante n'est pas réactivée. La prochaine expérience stratégique doit mesurer un calendrier concret et ses tâches concurrentes, pas réintroduire cette modification sous un autre nom.
