# K Pro — mesure et horizon CARE, premier lot du plan validé

## État de la livraison

Le banc officiel figé, le candidat autonome et les tests sont implémentés. Les deux banques sont COMPLETE : **4 400 matchs valides sur 400 graines distinctes**. Le candidat améliore le taux de résultat face à K Pro 6 sur les deux banques, mais la marge moyenne de confirmation reste incertaine. **Le double critère de promotion n’est pas satisfait : le candidat reste expérimental.**

Ce lot couvre A, B et un premier diagnostic pour C du plan K Pro. La planification économique, la coordination avancée, l’expansion et la robustesse face aux adversaires récents restent les étapes suivantes.

## Protocole et intégrité

Moteur et chargeur officiels conservés à l’identique au commit `28b6d8af3ce73926b3d0fda1410c1ddd8384ab8c`, avec licence et provenance. Configuration standard : 719 décisions par joueur, fin à J29 H23. Sources des témoins et adaptateur FP archivés inchangés. Le candidat ajoute exclusivement cet adaptateur à K Pro 6.

Banque A : 920000–920199. Banque B : 930000–930199, cinq duels et 2 000 matchs si déclenchée, comprenant le parent contre les autres témoins pour mesurer les régressions sur les mêmes graines. Protocole et critères fixés avant les résultats valides ; aucune retouche de politique pendant les tentatives ou entre les banques.

Les IC95 utilisent Student t199 sur 200 moyennes par graine après regroupement des deux sièges. Les adversaires restent séparés. Les mêmes graines fixent les scénarios initiaux ; les trajectoires de commerce peuvent diverger après les décisions des agents. Les différences face à un témoin regroupent également les deux sièges par graine. Les temps sont mesurés localement, sans certification du sandbox ou des délais Kaggle.

## Banque A

| Duel (marge du premier agent) | V / D / N | Taux¹ et IC95 | Marge moyenne et IC95 |
|---|---:|---|---|
| K Pro 4 corrigé / K Pro 2 | 212 / 188 / 0 | 53,00 % [46,76 ; 59,24] | 630,28 [250,40 ; 1010,17] |
| K Pro 6 / K Pro 2 | 188 / 212 / 0 | 47,00 % [40,53 ; 53,47] | -50,23 [-442,13 ; 341,68] |
| K Pro 6 / K Pro 4 corrigé | 201 / 199 / 0 | 50,25 % [43,98 ; 56,52] | -141,87 [-481,02 ; 197,29] |
| K Pro 6 + CARE FP / K Pro 6 | 230 / 168 / 2 | 57,75 % [52,85 ; 62,65] | 101,46 [55,81 ; 147,10] |
| K Pro 6 + CARE FP / K Pro 4 corrigé | 217 / 183 / 0 | 54,25 % [48,13 ; 60,37] | -44,94 [-383,09 ; 293,22] |
| K Pro 6 + CARE FP / K Pro 2 | 190 / 210 / 0 | 47,50 % [41,03 ; 53,97] | 26,36 [-360,22 ; 412,93] |

¹ Taux = (victoires + ½ égalités) / matchs. Il ne faut pas le confondre avec la proportion de victoires strictes. Chaque ligne contient 400 matchs sur les mêmes 200 graines.

Le candidat améliore K Pro 6 en duel direct sur cette banque : les deux bornes inférieures sont positives au-dessus de leurs seuils respectifs, 50 % pour le taux et 0 pour la marge. Ce résultat a déclenché la confirmation indépendante ; il ne suffit pas à désigner le meilleur agent global. Les incertitudes des confrontations entre références ne dégagent pas de supérieur général sur le taux de victoire. K Pro 4 a une marge positive contre K Pro 2, avec un intervalle de taux qui contient 50 %.

## Régressions appariées — banque A

Différence du candidat par rapport à K Pro 6, chacun jouant contre le même témoin :

| Témoin | Différence de marge et IC95 | Différence de taux, points de pourcentage et IC95 |
|---|---|---|
| K Pro 2 | 76,58 [26,54 ; 126,63] | 0,50 [-1,48 ; 2,48] |
| K Pro 4 corrigé | 96,93 [45,07 ; 148,79] | 4,00 [0,85 ; 7,15] |

Aucune borne supérieure n’est négative : le critère préenregistré de régression claire n’est pas déclenché. Les différences moyennes de marge sont positives ; ces valeurs n’attribuent pas à elles seules le gain à une activité précise de la ferme.

## Banque B et décision finale

La banque B est COMPLETE : 2 000 matchs, 200 nouvelles graines, sources strictement identiques à A.

| Duel (marge du premier agent) | V / D / N | Taux¹ et IC95 | Marge moyenne et IC95 |
|---|---:|---|---|
| K Pro 6 + CARE FP / K Pro 6 | 222 / 172 / 6 | 56,25 % [51,26 ; 61,24] | 39,96 [-10,17 ; 90,09] |
| K Pro 6 + CARE FP / K Pro 4 corrigé | 208 / 192 / 0 | 52,00 % [45,68 ; 58,32] | 2,90 [-328,98 ; 334,79] |
| K Pro 6 + CARE FP / K Pro 2 | 190 / 210 / 0 | 47,50 % [41,10 ; 53,90] | 80,40 [-300,67 ; 461,46] |
| K Pro 6 / K Pro 4 corrigé | 210 / 190 / 0 | 52,50 % [46,18 ; 58,82] | -19,31 [-349,42 ; 310,80] |
| K Pro 6 / K Pro 2 | 188 / 212 / 0 | 47,00 % [40,68 ; 53,32] | -6,96 [-376,18 ; 362,25] |

Le taux de résultat reste favorable au candidat face à son parent : 222 victoires, 172 défaites et 6 égalités, soit 56,25 % avec un demi-point par égalité. L’IC95 de ce taux reste au-dessus de 50 %. La marge moyenne de +39,96 a toutefois un IC95 de [−10,17 ; +90,09]. Sa borne inférieure n’est pas strictement positive.

**Décision : INCONCLUSIVE pour la promotion selon le double critère préenregistré. Le candidat reste expérimental.** Cette décision conserve le signal favorable sur les victoires ; elle ne démontre pas une absence d’effet. Les résultats de A et B ne sont pas regroupés pour contourner le critère indépendant.

Différences appariées en B, candidat moins parent contre le même témoin :

| Témoin | Différence de marge et IC95 | Différence de taux, points de pourcentage et IC95 |
|---|---|---|
| K Pro 2 | 87,36 [33,18 ; 141,54] | 0,50 [-1,82 ; 2,82] |
| K Pro 4 corrigé | 22,21 [-39,10 ; 83,53] | -0,50 [-3,29 ; 2,29] |

Aucune régression claire au sens du protocole n’est détectée contre les autres témoins. L’incertitude sur la marge du duel direct suffit à empêcher la promotion. Le candidat n’est ni intégré aux sources archivées ni soumis sur Kaggle dans ce lot.

## Diagnostic CARE et exécution

- K Pro 6 + CARE FP : 1200 participations, 0 commandes CARE classées trop tardives ; maximum local de décision 144,45 ms.
- K Pro 6 : 1200 participations, 15088 commandes CARE classées trop tardives ; maximum local de décision 188,18 ms.

En B, le candidat émet également zéro CARE trop tardif sur 1 200 participations ; K Pro 6 en émet 15 514 sur 1 200 participations. Le maximum local de décision est de 300,23 ms pour le candidat et 382,38 ms pour le parent. Ces mesures sous charge ne certifient pas les délais Kaggle.

Les tests mécaniques utilisent les productions du moteur officiel comme oracle, couvrent vache, mouton et oie ainsi que les frontières de calendrier, conservent les soins utiles et les tâches de nourriture/récolte/engrais. Le compteur mesure des commandes émises, pas une perte monétaire ni le nombre exact d’heures de travail converties en revenus. Le filtre conserve aussi la valeur retournée par la fonction de tâches du parent : l’effet sur les priorités doit être observé dans des traces avant toute modification supplémentaire.

La suite comprend 22 tests réussis, dont chargement officiel, autonomie du candidat, intégrité de l’archive, refus des mutations et actions invalides, statistiques groupées par graine, checksums et reprise sans rejouer des résultats déjà conservés. Les tests de reprise utilisent des données synthétiques explicitement séparées des campagnes. Un match réel de 719 décisions a aussi validé l’écriture et la relecture des checkpoints dans le dossier de travail.

## Incidents conservés et limites

La première tentative A a calculé 2 400 matchs mais n’a conservé que deux lignes visibles à la relecture ; le statut FAILED l’a exclue. Le remplacement d’un fichier encore ouvert reproduit ce mécanisme, sans que le déclencheur externe ait été identifié. La deuxième tentative, passée à une publication finale atomique, a été interrompue par une réinitialisation de l’environnement après au moins 1 000 calculs, avant publication. Elle est également exclue.

La campagne A retenue utilise des checkpoints atomiques fermés et vérifiés, une reprise explicite limitée aux matchs manquants et une relecture complète avant COMPLETE. Aucun résultat d’une tentative incomplète n’entre dans les tableaux. La reprise suppose un seul écrivain sur le dossier. Deux limites mineures sont documentées : arrêt tardif du pool après une erreur de match et fichier de génération pouvant rester vide si la lecture des sources échoue.

Le panel interne K Pro ne mesure pas le niveau des adversaires actuels du classement. La validation actuelle du moteur est locale ; le banc n’émule pas intégralement le framework Kaggle.

## Suite C proposée sur cette base

Conserver les trois témoins et le candidat expérimental. Le prochain diagnostic doit expliquer l’asymétrie entre victoires et pertes : en B, le gain moyen des 222 matchs gagnés est de 742,84 points, contre une perte moyenne de 865,85 points sur les 172 défaites. Ce constat est descriptif, sans attribution économique démontrée.

Commencer par les deux sièges des graines 930053, 930132 et 930051, dont les marges moyennes appariées sont respectivement −1 592, −1 317 et −1 027. Relier dans les traces la commande prévue, l’action exécutée, les stocks, les échéances de production, les trajets et les ventes réalisées. Vérifier en particulier la valorisation des tâches après retrait de CARE, puis choisir une seule correction selon la perte réellement observée. Ces graines sélectionnées après lecture des résultats deviennent des cas de diagnostic ; toute variante conçue à partir d’elles devra être confirmée sur de nouvelles graines indépendantes.

Les confrontations avec des adversaires récents compléteront ce contrôle interne avant de conclure sur la compétitivité au classement.

## Fichiers vérifiables

- [Protocole](../plans/2026-09-09-measure-care.md) et [commandes / limites](../evaluation.md).
- [Manifeste A](../../results/measure-care-a-durable/manifest.json), [résumé A](../../results/measure-care-a-durable/summary.json), [diagnostics A](../../results/measure-care-a-durable/diagnostics.json), [résultats bruts A compressés](../../results/measure-care-a-durable/matches.jsonl.gz).
- [Manifeste B](../../results/measure-care-b/manifest.json), [résumé B](../../results/measure-care-b/summary.json), [diagnostics B](../../results/measure-care-b/diagnostics.json), [résultats bruts B compressés](../../results/measure-care-b/matches.jsonl.gz), [décision calculée](../../results/measure-care-decision.json).
- [Première tentative rejetée](../../results/measure-care-a/manifest.json), [constat d’interruption de la deuxième](../../results/measure-care-a-retry/interruption.json).

Les octets JSONL décompressés doivent correspondre au SHA256 du manifeste. Les empreintes de toutes les sources utilisées sont également conservées dans ce manifeste.
