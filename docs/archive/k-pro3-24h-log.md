> Archive technique éditée pour cette publication. Ce document n’est pas un rapport de performance ni un statut actuel de livraison.

## 18:46–18:55 UTC — D terminé, prochaine question isolée

Audit marché/attentes terminé : le calcul mixte identifié concerne `idle_delivery=False` dans J6 ; ce n'est donc pas une cause de ses pertes. Le total après unités ne prouve pas une perte nocturne, puisque le marché peut libérer le stock. Correction supplémentaire après lecture officielle : les ouvriers sont réinitialisés au hangar chaque nuit ; le coût du détour porte sur les actions restantes du même jour, pas sur la position du lendemain. Rapport SDD corrigé, pas de drapeau activé.

## 19:18 UTC — G en préparation, pas encore lancé

F revue arithmétique indépendante PASS : tous les48 checkpoints, sources et totaux concordent. Aucune nouvelle partie. Analyse additionnelle des flux de blé :266 tours avec achat et vente exécutés, dont240 au jour0, le plus souvent une unité. Ces allers-retours peuvent être neutres ou bénéficier de l'autre joueur dans le marché lockstep ; leur suppression n'est pas une économie démontrée. L'hypothèse de culture basée seulement sur le stock brut n'est pas implémentée.

Task8 ajoutée au plan : nouvelle expérience bornée de priorité selon charge restante/temps disponible, hors ouverture et hors dernier jour. Le ratio service+distance minimale/capacité restante est un indice heuristique borné0,5..2, pas une borne exacte de tournées. Même macro, même ouverture J6, aucune modification achats/cultures/retours. Le recalcul de valeur marginale par ouvrier a déjà échoué dans candidate_feasible ; il n'est pas réintroduit. Préparation par workload_g_prepare, cinq nouveaux fichiers seulement, tests/revue/preuves avant lancement.

## 01:34–01:44 UTC — reprise effective, I lancé

Revue des preuvesH terminée PASS, chiffres recomputés ; seule note de provenance explicitée : le plan exact au lancement est conservé dans le préflight, le plan courant évolue.

## 02:29–02:55 UTC — diagnostic J terminé, espace libéré

Revue numériqueI PASS après correction explicite d'un faux positif : le compteur natif `produced` mesure les récoltes effectivement collectées, pas la croissance biologique. Soustraire les pertes, qui peuvent inclure des achats, aurait été incorrect. Chiffres évalués inchangés, aucun rejeu.

## État de reprise —06:20UTC, conservé comme historique

Task14/M préparation terminée puis revue NEEDS FIXES; **fix round1 fait, re-review par carrot_delay_m_review toujours EN COURS**. Aucun processusdejeu actif, Mbank nonjouée, toutesA..Lterminales. Ne pas recréer l'implémenteur, les smokes ou une banque. Attendre le verdictscopé puis traiter les éventuelsdéfauts; aucune campagneM avantaccordrevue. Agentcarrot_delay_m_prepare DONEfix1,rapport task-14-report.md completetlisibleaprèsincidentdeplaceholders corrigé.

## État de reprise —06:32UTC, conservé comme historique

En reprise, ne jamais relancer le lanceur initial à l'aveugle : vérifier processus/verrou/manifeste et tous les fichiers cells ET staging. Ne rejouer aucun fichier valide, y compris un staging achevé non encore déplacé. Les32argv et la fermeture source sont dans le manifeste. Ne reprendre que des paires manquantes après interruption purement infrastructure et vérification complète. Un index terminal interdit toute reprise.

## Dernier état de reprise — demande utilisateur TOMATO N, campagne active

Amendement de protocole documenté **avant toute donnée N100** : ces contrôles inactifs autorisent seulement l'exploration gelée de la fréquence d'utilisation et du résultat ; la preuve active achat→plantation→récolte→vente reste manquante et interdit sélection/certification tant qu'elle n'est pas obtenue indépendamment. Ne pas dire que les quatre NO_TRIGGER ont validé le cycle tomate. L'utilisateur a été informé de cette limite. Aucun changement du code, doses ou seuil.

## Reprise09:30UTC — préparation O et nouveau point Kaggle

Attention ressources : système retombé à~787MiB libres malgré l'espace libéré auparavant, externe137GiB, RAM3,4GiB disponible, swap presque plein. Ne pas augmenter le parallélisme ; O au plus2 paires, données externes et seuils d'arrêt originaux. Aucune donnée personnelle supprimée, aucune demande5Go renouvelée. Deadline/final100 inchangés.

## Dernier état de reprise — O lancé,09:54UTC

En reprise : vérifier processus/verrou et tous les fichiers claim/reference/candidate/pair/éventuelindex ou controller-result. **Ne pas relancer le lanceur initial** : il refuse tout ancien claim ou index. Ne rejouer aucune branche valide, même si sa paire est incomplète. Une interruption purement infrastructure exige validation de toute fermeture et récupération explicite du seul suffixe; un rejet sémantique bloque la confirmation. Attendre index32paires ; PASS_ACTIVE_GATES nécessite au moins un cycle exécuté complet avec différences actives à chaque siège. NO_TRIGGER/LIFECYCLE_UNOBSERVED restent honnêtes.

## État prioritaire de reprise — P interrompu, défaut noyau NTFS3 confirmé

**ARRÊT DE SÉCURITÉ : aucun calcul et aucune écriture expérimentale sur DePal dans ce boot.** Ne pas relancer P parce que l'erreur est infrastructure ; l'état du noyau/stockage doit d'abord être assaini. Demander à l'utilisateur un redémarrage coordonné, puis contrôler noyau/montage et intégrité avant éventuelle reprise. Un simple nouveau boot ne prouve pas que le défaut NTFS3 est corrigé. Aucun démontage, fsck/réparation, changement de pilote/noyau ou reboot autonome autorisé. Rapport détaillé local `docs/k-pro3-tomato-p-infrastructure-stop.md`.

## État prioritaire — récupération autorisée, P repris et progression validée

Anomaliejournal conservée : l'ancienne ligne480contient18octetsNUL àl'emplacement de l'écriture interrompue ducrashNTFS3, visiblesaprèsremontage. AucunNUL danslesnouvelleslignes àpartir576. Ne pasréécrirel'historique : checkpointsJSON complets restent lasourcedevérité, indépendantsdecejournalinformatif. Ceconstatn'estpasunenouvelleerreurdejeu.

Automationexistante miseàjour avecgardeFUSE obligatoireavanttoutereprise. Aucunreboot/remontage automatique aprèsnouvellepanne ; aprèsredémarragedéfautpeutredevenirNTFS3. Deadline16:55:39UTC/arrêtexploration15:55:39UTC inchangés. Root~606MiBaucontrôle etguard300MiBtoujoursactif;nepascontournerparnettoyagepersonnel. Prochainetravail : suivreP, puiscompare_frozen/selection_audit/behavior surdeuxmatricesterminales etrevue;Task5final100distincttoujoursenattente. Aucunautrerun, promotionsoumissionmodificationRLouincumbent.

## État prioritaire — P terminé et relu, final Q gelé en préflight

Revue bornée de lancement en cours : agent /root/final_q_launch_review, brief/report/package task-5-final-q-* dans le workspaceSDD. Attendre verdict puis vérifier immédiatement FUSE/dev/sda2, taint0/absenceBUG-Oops-stockage, ressources et verrous/processus avant lancement du runner inchangé. Les messages firmware ACPI existent : ne pas prétendre journal noyau totalement vide; pas de nouveau BUG NTFS3 observé sous FUSE. Source/config/protocole Q maintenant figés, ne pas les modifier selon le résultat final. Namespace final-q-100 absent au préflight, aucun jeu final encore joué.
