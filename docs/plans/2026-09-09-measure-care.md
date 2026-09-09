# K Pro — démarrage du plan validé : mesure et horizon CARE

## Autorité et périmètre

L'utilisateur a validé le plan K Pro A–G dans cette conversation. Exclusivement série K Pro. Première livraison concrète : A (banc reproductible), B (correction CARE isolée), et diagnostic permettant de choisir la suite C. D–G sont des étapes conditionnées par ces preuves, pas des fonctionnalités réputées intégrées. Les témoins archivés et SOURCE_HASHES.json restent inchangés. Dépôt source : 73deafcf04164c5d493909ab6d7bd31a39a79876. Opérations distantes par le plugin GitHub. Publication d'une branche et PR ; ni fusion ni soumission Kaggle à ce stade.

## Protocole décidé avant résultats

- Standard moteur officiel : 720 états, 719 décisions par joueur, 24 tours/jour, capacité100. Sources officielles figées à 28b6d8af3ce73926b3d0fda1410c1ddd8384ab8c ; sources, licence et empreintes incluses pour exécution hors réseau.
- Banque A : 920000–920199, exactement 200 seeds, les deux sièges pour chaque duel. Références K Pro 2, K Pro 4 corrigé, K Pro 6. Comparer les trois paires. Le choix est descriptif si les IC ne permettent pas de distinguer les versions ; conserver les témoins dans ce cas.
- Candidat CARE : exclusivement appliquer l'adaptateur FP existant à K Pro 6 dans un fichier autonome expérimental. Aucun autre changement de politique. Banque A : candidat contre les trois témoins. Mêmes seeds pour une comparaison sur les mêmes scénarios initiaux, sans supposer la ville identique.
- Si signal favorable (taux global supérieur à50% et marge positive contre le parent, sans dégradation claire contre les autres), confirmer sans retouche sur banque B 930000–930199. Sinon ne pas consommer B et conserver candidat expérimental. Signal favorable n'est pas promotion.
- Dégradation claire contre un autre témoin : comparer candidat et parent contre ce même témoin, sur les mêmes seeds et sièges ; une borne supérieure IC95 de la différence de marge ou de taux strictement négative bloque la confirmation/promotion. Ces différences sont regroupées par seed, sans considérer les commerces finaux comme constants. Précision enregistrée avant le lancement de A.
- Banque B, si déclenchée : cinq paires sur les200 nouvelles seeds et les deux sièges, soit2000 matchs : candidat contre les trois témoins, plus K Pro6 contre K Pro2 et K Pro4 corrigé. Ces deux dernières paires permettent de calculer la régression appariée sur la banque de confirmation elle-même. Précision enregistrée avant tout résultat valide de A.
- Promotion : confirmation indépendante, borne inférieure IC95 du taux >50% et borne inférieure de marge >0 contre parent, absence de problème mécanique/runtime et pas de régression claire contre les autres témoins. Sinon INCONCLUSIVE ou REJECTED selon preuves, jamais promotion automatique.
- Statistiques sur 200 moyennes par seed pour les deux sièges (Student199). Plusieurs adversaires : pas de pooling prétendu indépendant. Relevés de temps locaux uniquement, pas certification sandbox Kaggle.
- Reprise opérationnelle ajoutée après interruption de l’environnement : checkpoints atomiques par match ; reprise explicite des seuls matchs manquants avec identité complète inchangée, un seul écrivain à la fois. Aucun résultat validé n’est écrasé. Ce changement ne modifie pas le protocole statistique.
- Campagnes immuables : identité sources/config/seeds, résultats par match, échec explicite si erreur ou résultat manquant ; aucun écrasement. Aucun token dans les fichiers.

### Task 1: candidat CARE et tests mécaniques

Créer evaluation/build_candidate.py, candidates/k_pro6_care_fp.py et tests/test_care_candidate.py. Utiliser exclusivement le parent k_pro/k_pro6.py et l'adaptateur research/pro6-next/care_horizon_fp.py, tous deux archivés inchangés. Le générateur produit un candidat standard-library autonome, reproductible, refuse d'écraser un fichier existant, et préserve le dernier callable choisi par Kaggle. Aucun import du dépôt pendant l'exécution du candidat.

Tests : reproduire le défaut sur parent avec moteur officiel avant correction ; vérifier l'effet nul du soin tardif sur les produits disponibles jusqu'àJ29, préserver les soins utiles, conserver nourrissage/récolte/engrais dans les tâches modifiées, couvrir vache/mouton/oie, frontières calendrier et chargement du fichier autonome par la vraie fonction officielle get_last_callable. Tester autonomie depuis répertoire temporaire vide, non-mutation, indépendance des états entre instances. Le test doit observer un échec comportemental sur le parent et réussir sur le candidat ; pas de duplication de formule pour calculer l'oracle.

Interfaces fournies par Task2 (root) : evaluation.engine.load_engine() -> module officiel ; evaluation.engine.load_policy(path) -> callable chargé ; evaluation.engine.new_game(seed) -> (state,env) ayant observations accessibles comme dictionnaires/attributs et configuration standard. Les tests peuvent utiliser les helpers natifs du moteur pour avancer les nuits. Ne pas modifier evaluation/engine.py ni autres fichiers de Task2. Rapport TDD et limites dans le workspace SDD. Pas de lancement de campagnes lourdes.

### Task 2: banc reproductible

Créer evaluation/engine.py, evaluation/campaign.py, tests/test_evaluation.py, vendor/kaggriculture/ avec sources officielles/licence/provenance. Loader vérifie empreintes avant exécution, conserve sources officielles non modifiées et ne pollue pas sys.modules. Agent reçoit copie indépendante observation et configuration ; seed caché, schéma et non-mutation contrôlés. Match emploie condition terminale officielle, isole les politiques entre matchs/sièges et rapporte actions, horaires CARE inutiles, temps et contexte public.

Runner en processus avec nombre de workers borné ; campagne imposant exactement200 seeds et les deux sièges, noms de politiques explicites, manifestes de sources/moteur/config/seeds, résultats par match, résumé avec IC par seed et siège. Sortie exclusive, statut COMPLETE seulement après validation de toutes les clés attendues, fichiers et politique inchangés. Tests réels ciblant détection résultat dupliqué/manquant, regroupement par seed, schéma invalide/mutation, frontière loader et terminaison, intégrité des sources. Réseau interdit pendant match. Documenter limites de l'orchestration vs framework distant.

### Task 3: campagnes, diagnostic et livraison

Exécuter les tests, campagne A puis B uniquement si sa condition est satisfaite. Publier résultats bruts, résumés, commandes reproductibles et rapport en français ; comparer à la baseline sans récit causal non démontré. Préserver le journal de décision. Faire relire le code et corriger les défauts bloquants. Publier une PR via plugin GitHub avec base revalidée. Ne pas fusionner ni soumettre sur Kaggle.

## Suite du plan validé

C : identifier pertes réelles et contraintes dominantes. D : sélectionner une décision économique bornée sur cette preuve. E : réservations et séquences d'ouvriers. F : composition productive et expansion. G : robustesse aux situations de marché et aux adversaires récents. Aucun RL ni référence Apex dans ce périmètre.
