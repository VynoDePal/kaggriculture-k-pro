# Diagnostic économique après retrait de CARE

## Conclusion bornée

Les six replays choisis après la banque B ne justifient ni promotion ni conclusion générale de performance. Ils établissent toutefois un mécanisme précis sur la graine 930053 : à J28 H0 (step 672), le candidat vend quatre tomates dans l'emplacement 1 pendant que le parent commence ses fraises. La résolution unitaire et simultanée du marché abaisse alors le premier prix de fraise du candidat de 82 à 24. Le candidat réalise 178 points sur 29 fraises, contre 1 614 sur 30 pour le parent, soit −1 436 de recette fraise à cette étape.

Un contrôle causal limité à cette étape échange seulement les emplacements 1 et 2 du candidat. Toutes les quantités, achats, embauches, positions d'emplacements et actions adverses restent enregistrés. Le cash après l'étape passe de `[92289, 93766]` à `[93027, 93069]` : +738 pour le candidat, −697 pour l'autre ferme et +1 435 de marge relative. Les fermes hors cash et les stocks en remise sont identiques après les deux branches. Cela prouve un effet d'ordre dans cette étape, pas une amélioration sur une partie complète ni la récupération exacte d'une « perte » contrefactuelle de 1 436.

Les cinq autres replays ne montrent pas une cause commune établie. La seule hypothèse prioritaire pour D est donc une ordonnance des ventes sensible à la perte de profondeur du marché, testée sur une nouvelle banque indépendante.

## Méthode et fidélité

`evaluation/diagnose.py` réinjecte les actions enregistrées dans l'interpréteur officiel inchangé. Des observateurs passifs entourent `_commit_unit`, `_do_hire` et `_do_buy_land`; seuls les commits réussis alimentent la comptabilité. Chaque pré-état et chaque post-état est comparé à la trace.

- 6 parties B consommées, 719 étapes chacune ; 8 628 post-états joueur vérifiés exactement.
- 12 soldes finaux réconciliés sans résidu : cash initial 3 000 + ventes − achats/embauches/terrains = cash terminal.
- Les deltas nets entre étapes et les prix cotés ne sont jamais utilisés comme recettes brutes.
- Les commandes demandées restent distinctes des commits observés et du contrôle causal isolé.

Les empreintes SHA-256 de chaque trace consommée figurent dans `results/diagnose-care-analysis-final.json`. Le JSON contient les agrégats par produit/opération, 24 groupes d'étapes localisables par partie, les stocks terminaux, les divergences initiales et le contrôle d'ordre.

## Bilan des six replays B

Les valeurs ci-dessous sont du point de vue du candidat CARE FP. « Coûts » additionne les commits signés hors ventes (achats, animaux, graines, embauches et terrains).

| Graine | Siège | Marge | Δ ventes | Coûts candidat / parent | Δ fraises | Première divergence d'action |
|---:|---:|---:|---:|---:|---:|---|
| 930051 | 0 | −1 517 | −1 053 | −28 994 / −28 530 | −1 095 | J3 H15, step 87 |
| 930051 | 1 | −537 | −1 078 | −28 473 / −29 014 | −354 | J3 H15, step 87 |
| 930053 | 0 | −1 592 | −1 498 | −27 808 / −27 714 | −1 436 | J26 H0, step 624 |
| 930053 | 1 | −1 592 | −1 498 | −27 808 / −27 714 | −1 436 | J26 H0, step 624 |
| 930132 | 0 | +1 333 | +839 | −26 268 / −26 762 | +1 400 | J5 H9, step 129 |
| 930132 | 1 | −3 967 | −3 589 | −26 684 / −26 306 | −3 239 | J5 H9, step 129 |

Sur 930053, les actions restent identiques jusqu'à la première divergence, `PICKUP WHEAT 3` contre `PICKUP WHEAT 2`, au step 624. Les cases des fermes divergent toutefois dès le step 312 (J13 H0) sous l'effet de la trajectoire du moteur; elles ne sont donc pas présumées identiques jusque-là. Le cash reste identique à 79 207 au step 624. À J27 H0 il vaut 82 461 contre 82 418, puis 87 664 contre 88 067 à J28 H0 et 92 433 contre 93 932 à J29 H0. L'essentiel de l'écart final existe donc avant le dernier jour. Le mécanisme step 672 explique presque toute la différence de recettes de fraises observée, sans démontrer que le retrait de CARE est sa cause unique.

Les douze fermes terminent sans marchandise en remise, sans inventaire porté et sans rendement restant sur une case. Quelques graines non utilisées restent selon la trajectoire. Une liquidation terminale simple des marchandises n'est donc pas soutenue par ces cas.

## Contrôles parent contre lui-même

Ces trois parties conservent les deux fermes et utilisent K Pro6 des deux côtés. Elles ne sont pas des lignes B, ni un test de performance.

| Graine | Siège 0 | Siège 1 | Écart initial/trajectoire |
|---:|---:|---:|---:|
| 930053 | 103 543 | 103 543 | 0 |
| 930132 | 85 832 | 83 483 | +2 349 |
| 930051 | 104 299 | 103 833 | +466 |

Le contrôle 930132 montre que l'écart de sièges peut être substantiel sans CARE FP. Il interdit d'attribuer directement les +1 333/−3 967 du candidat à une cause commune. Les commerces ultérieurs peuvent aussi diverger : le RNG de fin de journée est partagé entre mauvaises herbes et tirage de ville, et des cases vides différentes changent sa consommation.

## Valorisation des tâches

La lecture du `reference.py` réellement embarqué dans K Pro6 donne deux faits distincts. `animal_tasks` valorise le produit déjà disponible et l'urgence alimentaire; il n'ajoute pas explicitement CARE. À partir de J6, `tasks` combine cependant cette valeur à 50 % avec `incremental_task_value` à 50 %, qui valorise explicitement CARE au prix du produit. FP retire CARE de la séquence : la composante marginale et donc certaines priorités changent déjà. Dire que les priorités restent inchangées serait faux.

`act_units` filtre ensuite des commandes selon l'inventaire du travailleur tout en conservant la valeur pré-filtrage pour l'urgence et les coûts. C'est un décalage général plausible entre décision et valeur, mais aucun des six replays ne l'établit comme cause commune des pertes.

## Hypothèse D et expérience falsifiable

Hypothèse unique : **à quantités de vente existantes identiques, ordonner les seuls emplacements `SELL` selon la perte réalisable induite par la profondeur publique du marché réduit les pertes de revenu dues aux courses de résolution simultanée.** La future politique doit utiliser exclusivement les observations publiques et ses propres stocks; le diagnostic, qui peut voir les deux inventaires privés, ne doit pas fuiter cette information. Le tri actuel par prix unitaire existe déjà : D doit modéliser la valeur totale réalisable et la profondeur, pas simplement réintroduire ce tri.

Expérience bornée : partir de K Pro6 inchangé et créer une variante qui permute uniquement les emplacements `SELL` existants, en conservant quantités, achats, embauches, terrains et positions vides. CARE FP reste une expérience séparée : il n'est ni ajouté ni retiré dans ce duel d'isolation. Valider mécaniquement l'invariance hors ordre, puis comparer cette variante figée à ce parent K Pro6 exact sur une nouvelle banque de confirmation choisie avant résultats, deux sièges par graine.

Critères indépendants : (1) aucune information privée adverse; (2) aucune commande non-vente déplacée ou quantité modifiée; (3) seuils de promotion préenregistrés — borne inférieure de l'IC95 de marge strictement supérieure à 0 et borne inférieure du taux strictement supérieure à 50 % — sur la nouvelle banque; (4) absence de régression claire contre les témoins retenus. Un échec mécanique falsifie la variante. Un intervalle franchissant le seuil rend le résultat inconclusif, pas l'hypothèse économique fausse; la taille de banque et la puissance devront être fixées avant résultats. Le +1 435 d'une seule étape sert uniquement de preuve de mécanisme.

## Limites

Les graines ont été choisies après résultats. Les transactions observées prouvent des flux réalisés, pas la valeur économique contrefactuelle d'une tâche ni la causalité générale de CARE FP. Le contrôle d'ordre ne poursuit pas la partie; il ne capture ni décisions futures ni changement de RNG. Les résultats 930051 et 930132 restent descriptifs. Aucune politique, campagne A/B, décision de promotion, source vendor ou K Pro6 n'a été modifiée.

## Artefacts

- [Analyse reproductible](../../results/diagnose-care-analysis-final.json)
- [Contrôles parent-self](../../results/diagnose-care-controls-final/summary.json) et leurs trois replays compressés dans le même dossier
- [Six replays B](../../results/diagnose-care-c/summary.json)
- [Protocole de replay et commandes](../evaluation.md)
