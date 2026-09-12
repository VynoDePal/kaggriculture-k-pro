# K Pro 6 — protocole de mesure de la priorité des ventes

Protocole fixé avant les résultats. Design approuvé dans la conversation : classement stable des ventes par recettes menacées si un concurrent vend d'abord la même quantité. Ce scénario ne prédit pas son inventaire. Parent : K Pro6 inchangé, sans CARE FP. Seuls les emplacements SELL sont permutés ; quantités, actions des unités, autres ordres et emplacements vides conservés. Candidat autonome `candidates/k_pro6_sale_pressure.py`.

Pour chaque ordre de q unités : simuler 2q ventes unitaires avec les paramètres publics du moteur figé, ses arrondis et son plancher (l'offre n'augmente pas pour une vente à1). Priorité = somme des q premiers prix moins somme des q suivants. Aucun paramètre ajusté aux replays ; égalités départagées par ordre initial. La quantité q est celle déjà demandée par le parent. Les décisions suivantes pourront naturellement diverger si les recettes changent.

## Banques et critères

- A :940000–940199, exactement200 graines, les deux sièges pour chaque paire.
- Cinq paires : candidat/KPro6, candidat/KPro4 corrigé, candidat/KPro2, KPro6/KPro4 corrigé, KPro6/KPro2. Soit2000 matchs par banque. Les deux dernières mesurent les régressions appariées contre un même témoin.
- Signal favorable A : taux (victoires+½égalités)/matchs >50%, marge moyenne>0 face au parent, aucune régression claire contre les témoins. Sinon B reste inutilisée.
- B conditionnelle :950000–950199, mêmes cinq paires, mêmes sources, aucun réglage entre banques. 2000 matchs supplémentaires si déclenchée.
- Promotion uniquement si en B la borne inférieure IC95 du taux>50% ET de marge>0 contre le parent, sans anomalie mécanique/runtime ni régression claire contre les témoins.
- Régression claire : différence candidat moins parent face au même témoin, groupée par graine sur les deux sièges ; borne supérieure IC95 de marge ou taux<0. IC Student199 sur200 moyennes par graine, adversaires séparés. Pas de regroupement A+B pour contourner B.
- Échec de seuil sans preuve négative : résultat inconclusif, pas preuve d'absence d'effet. Aucun ajout opportuniste de graines pour franchir le seuil. La puissance pour de petits effets peut être insuffisante à200 graines.

## Intégrité et limites

Utiliser le banc existant, moteur officiel figé, sorties exclusives et checkpoints vérifiés. Figer les empreintes avant A et les conserver entre A/B. Les cas930053/930132/930051 restent des diagnostics, jamais une confirmation. Conserver archives, CARE, vendor et anciennes campagnes inchangés. Aucun merge ni soumission Kaggle. Le panel K Pro ne mesure pas la compétitivité contre les adversaires actuels du classement ; les temps locaux ne certifient pas le sandbox distant.
