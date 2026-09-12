# Priorité des ventes sous pression — mesure figée

## Décision

Le candidat expérimental `candidates/k_pro6_sale_pressure.py` satisfait les critères de promotion pré-enregistrés sur la banque de confirmation B. Face à K Pro 6, les bornes inférieures IC95 sont de **92,10 %** pour le taux de résultat et de **+4 416,08** pour la marge : elles dépassent respectivement 50 % et zéro. Aucun delta apparié contre K Pro 4 corrigé ou K Pro 2 n'indique une régression claire.

Cette décision vaut uniquement sur le panel interne de témoins K Pro archivés. Elle ne remplace pas `k_pro/k_pro6.py`, ne déclenche ni soumission ni publication Kaggle, et ne démontre pas une compétitivité face aux adversaires actuels du classement.

## Changement mesuré

Le candidat conserve K Pro 6 et permute seulement les emplacements SELL déjà produits. Pour une vente de quantité *q*, il simule le scénario public où le concurrent vend d'abord la même quantité, puis classe les ordres par recettes menacées. Quantités, actions des unités, autres ordres et emplacements vides sont conservés. Ce scénario de rival à quantité identique est une mesure de pression, pas une prévision de son inventaire.

Le [protocole fixé avant résultats](../sale-pressure-protocol.md) réserve A (940000–940199) au screening et B (950000–950199) à la confirmation, avec cinq paires, deux sièges et 200 graines par banque. Aucun réglage n'a eu lieu entre A et B.

## Résultats par paire

Les taux comptent une égalité pour un demi-point. Les IC95 sont des IC Student t199 sur les 200 moyennes par graine, chaque moyenne réunissant les deux sièges.

### Banque A — screening

| Paire (premier moins second) | V-D-N | Taux, IC95 | Marge moyenne, IC95 |
|---|---:|---:|---:|
| candidat / K Pro 6 | 378-22-0 | 94,50 % [91,64 ; 97,36] | +4 694,24 [4 284,65 ; 5 103,82] |
| candidat / K Pro 4 corrigé | 374-26-0 | 93,50 % [90,35 ; 96,65] | +4 436,15 [4 038,11 ; 4 834,18] |
| candidat / K Pro 2 | 380-20-0 | 95,00 % [92,38 ; 97,62] | +4 827,98 [4 408,43 ; 5 247,53] |
| K Pro 6 / K Pro 4 corrigé | 177-223-0 | 44,25 % [37,84 ; 50,66] | -195,85 [-538,70 ; 147,01] |
| K Pro 6 / K Pro 2 | 189-211-0 | 47,25 % [40,87 ; 53,63] | +93,02 [-293,49 ; 479,53] |

A dépasse 50 % et zéro face au parent, sans régression claire contre les témoins : le déclenchement conditionnel de B était donc justifié.

### Banque B — confirmation indépendante

| Paire (premier moins second) | V-D-N | Taux, IC95 | Marge moyenne, IC95 |
|---|---:|---:|---:|
| candidat / K Pro 6 | 379-21-0 | 94,75 % [92,10 ; 97,40] | +4 854,00 [4 416,08 ; 5 291,91] |
| candidat / K Pro 4 corrigé | 374-26-0 | 93,50 % [90,68 ; 96,32] | +4 188,99 [3 791,95 ; 4 586,02] |
| candidat / K Pro 2 | 381-19-0 | 95,25 % [92,49 ; 98,01] | +4 952,77 [4 532,44 ; 5 373,10] |
| K Pro 6 / K Pro 4 corrigé | 182-218-0 | 45,50 % [39,24 ; 51,76] | -138,88 [-452,14 ; 174,39] |
| K Pro 6 / K Pro 2 | 195-205-0 | 48,75 % [42,29 ; 55,21] | +93,05 [-270,70 ; 456,79] |

## Comparaisons appariées aux témoins

Chaque delta est « candidat moins K Pro 6 » face au même témoin, apparié par graine et siège puis moyenné par graine. Une régression claire exigerait une borne supérieure sous zéro ; ici, toutes les bornes inférieures sont positives.

| Banque | Témoin | Delta taux, IC95 | Delta marge, IC95 |
|---|---|---:|---:|
| A | K Pro 4 corrigé | +49,25 points [42,46 ; 56,04] | +4 631,99 [4 166,04 ; 5 097,95] |
| A | K Pro 2 | +47,75 points [41,41 ; 54,09] | +4 734,96 [4 246,27 ; 5 223,65] |
| B | K Pro 4 corrigé | +48,00 points [41,38 ; 54,62] | +4 327,86 [3 866,25 ; 4 789,47] |
| B | K Pro 2 | +46,50 points [39,96 ; 53,04] | +4 859,72 [4 369,54 ; 5 349,91] |

Les gains observés sont donc des gains contre des témoins archivés dans ce banc précis. Les deux banques ne sont pas regroupées pour franchir les seuils : la confirmation et la décision utilisent B seule.

## Intégrité et reproductibilité

Chaque banque contient exactement 2 000 matchs complets et des graines disjointes. A et B partagent les mêmes empreintes de candidat, parent, témoins, moteur, builder et modules d'évaluation. L'adaptateur est embarqué dans le candidat, dont l'empreinte SHA-256 est `eeda027a771109421fd10ebedf5fcb21cef4a1e379a1ec1cc3af73135ac3761d`; le builder `evaluation/build_sale_candidate.py` porte `38243301b583768821eafb9a37aa0fc071b42d2fca3e9a0a83c1eeba101b5bed`. Python 3.12.14 et huit workers ont été enregistrés. Avant campagne, les 40 tests passaient en 37,069 s. Après production et avant publication, la suite complète repasse : 40 tests réussis en 39,374 s avec Python 3.12.14.

Reconstruction sans écraser le candidat publié, puis reproduction dans des destinations neuves :

```bash
python -m evaluation.build_sale_candidate /tmp/k_pro6_sale_pressure_rebuilt.py
python -m evaluation.campaign --seed-start 940000 --workers 8 \
  --pair candidates/k_pro6_sale_pressure.py k_pro/k_pro6.py \
  --pair candidates/k_pro6_sale_pressure.py k_pro/k_pro4_loader_fixed.py \
  --pair candidates/k_pro6_sale_pressure.py k_pro/k_pro2.py \
  --pair k_pro/k_pro6.py k_pro/k_pro4_loader_fixed.py \
  --pair k_pro/k_pro6.py k_pro/k_pro2.py --output /tmp/sale-pressure-a-new
python -m evaluation.campaign --seed-start 950000 --workers 8 \
  --pair candidates/k_pro6_sale_pressure.py k_pro/k_pro6.py \
  --pair candidates/k_pro6_sale_pressure.py k_pro/k_pro4_loader_fixed.py \
  --pair candidates/k_pro6_sale_pressure.py k_pro/k_pro2.py \
  --pair k_pro/k_pro6.py k_pro/k_pro4_loader_fixed.py \
  --pair k_pro/k_pro6.py k_pro/k_pro2.py --output /tmp/sale-pressure-b-new
```

Les flux JSONL décompressés ont respectivement les SHA-256 `0bf1118594c62c1577de259c9d09c5ce2b3d6d3e9a185a1a5302d09c81da262d` (A) et `1047bc05d30b0151924591293f29f7f74d53f70df70f196273c63500f9707dad` (B). Ce snippet en lecture seule vérifie ces empreintes et recalcule les différences appariées sans dépendre d'un script local :

```bash
python - <<'PY'
import gzip, hashlib, json, statistics
from pathlib import Path

for bank in ('a', 'b'):
    folder = Path(f'results/sale-pressure-{bank}')
    raw = gzip.decompress((folder / 'matches.jsonl.gz').read_bytes())
    manifest = json.loads((folder / 'manifest.json').read_text())
    assert manifest['status'] == 'COMPLETE'
    assert hashlib.sha256(raw).hexdigest() == manifest['results_sha256']
    rows = [json.loads(line) for line in raw.splitlines()]
    assert len(rows) == 2000
    by_pair = {}
    for row in rows:
        by_pair.setdefault((row['candidate'], row['opponent']), {})[
            row['seed'], row['seat']] = row
    candidate, parent = 'candidates/k_pro6_sale_pressure.py', 'k_pro/k_pro6.py'
    score = lambda row: 1 if row['margin'] > 0 else .5 if row['margin'] == 0 else 0
    for witness in ('k_pro/k_pro4_loader_fixed.py', 'k_pro/k_pro2.py'):
        c, p = by_pair[candidate, witness], by_pair[parent, witness]
        margins, rates = [], []
        for seed in manifest['seeds']:
            margins.append(statistics.mean(c[seed, s]['margin'] - p[seed, s]['margin'] for s in (0, 1)))
            rates.append(statistics.mean(score(c[seed, s]) - score(p[seed, s]) for s in (0, 1)))
        print(bank, witness, statistics.mean(rates), statistics.mean(margins))
PY
```

Les fichiers `manifest.json`, `summary.json`, `diagnostics.json` et `matches.jsonl.gz` de chaque banque constituent la preuve publiée. La décision structurée est dans `results/sale-pressure-decision.json`.

## Limites

Le moteur officiel figé est orchestré localement : les durées locales ne certifient ni le sandbox ni la limite de temps distante. Les comptes de commandes décrivent des actions émises, pas une attribution économique causale. Les cas diagnostiques 930053, 930132 et 930051 restent des contre-exemples exploratoires et ne contribuent pas à cette confirmation. Une trajectoire peut diverger après modification des recettes ; le panel ne permet donc ni forecast du rival ni généralisation au ladder actuel.
