# K Pro — diagnostic des défaites après priorité des ventes

## Conclusion et périmètre

Le premier tri des ventes est favorable dans les trois cas examinés. Une sensibilité des achats au cash est établie : un faible changement de trésorerie peut déclencher une vache de400 pièces et faire diverger ensuite les décisions. **La causalité de la défaite terminale n'est pas établie.** Aucune politique n'est modifiée et aucun nouveau gain de performance n'est revendiqué.

Le [protocole](../diagnose-sale-pressure-protocol.md) sélectionne les trois pires moyennes par graine contre K Pro6 dans B, soit six des21 défaites sur400 matchs. Sélection extrême, non représentative ; ni fréquence générale des mécanismes, ni mesure du classement actuel. La validation précédente reste inchangée.

Point de départ distant : PR3 fusionnée en `49aa95faff0b57132da737292583618638a349f1`, arbre `a4520652c37f59db4e827f64a953a9a38db9f9c8`. Les fichiers Python, le moteur et les campagnes précédentes sont inchangés. Les empreintes embarquées dans chaque trace identifient ces sources.

## Preuves contrôlées

Six replays candidat/parent reproduisent exactement les scores B. Trois contrôles parent-self ont leur score calculé séparément par le runner, puis vérifié par le replay. Le diagnostic des neuf traces vérifie12942 post-états de joueur et18 réconciliations de cash, toutes à zéro d'écart. Les18 fermes terminent sans marchandises dans le hangar, les inventaires portés ou les rendements encore sur case ; certaines graines inutilisées restent présentes.

Validation locale : `python -m unittest discover -s tests`,40 tests réussis en39,070s sous Python3.12.14. Les neuf SHA de traces, les719 pas de décision par trace, les scores et identités de sources ont aussi été vérifiés.

| Graine | Candidat / parent, candidat au siège0 | Marge aux deux sièges | Contrôle parent / parent |
|---|---:|---:|---:|
|950080|114923 /116935|−2012 /−2012|141097 /141097|
|950000|138017 /139925|−1908 /−1908|126756 /126756|
|950180|90418 /91789|−1371 /−1371|93851 /93851|

Les contrôles égaux affaiblissent l'explication par une asymétrie initiale/de siège seule. Leurs scores absolus ne constituent pas une estimation de gain de politique : les trajectoires et le RNG des commerces peuvent diverger lorsque l'occupation du sol change.

## Premier embranchement : un meilleur prix, puis un autre achat

Dans les trois matchs avec candidat au siège0, la première différence d'action est au pas120 (J5 H0) : le candidat vend WHEAT20 avant FERTILIZER4, le parent fait l'inverse. Les quatre HIRE restent aux mêmes emplacements.

Un échange isolé des deux SELL du candidat, au même pré-état et avec les actions adverses fixées, donne :

| Graine | Cash après tri candidat | Cash après ordre inversé | Effet du tri sur cash propre | Effet du tri sur marge relative |
|---|---:|---:|---:|---:|
|950080|1345 /1308|1329 /1329|+16|+37|
|950000|1345 /1308|1329 /1329|+16|+37|
|950180|1366 /1338|1354 /1354|+12|+28|

Fermes hors cash et hangars identiques entre les deux branches de ce contre-test. Il s'agit d'un seul tour, pas d'un contrefactuel de partie entière. L'hypothèse « le premier tri perd directement des recettes » est réfutée pour ces trois tours ; cela ne juge pas tous les tris ultérieurs.

Au pas132 (J5 H12), première différence d'ordre non-SELL : le candidat achète une vache, le parent n'achète pas. Les actions des unités restent identiques entre les deux joueurs à cet instant.

Deux instances fraîches du candidat reçoivent exactement son historique jusqu'au pas131. Au pas132 uniquement, une instance reçoit un cash propre modifié ; l'autre reproduit l'action archivée. Configuration et autres observations restent identiques. L'action originale est vérifiée à chaque pas.

| Graine | Cash original : achat | Cash ramené à celui du rival : achat | Cash diminué du seul gain propre au pas120 : achat |
|---|---|---|---|
|950080|540 : oui|503 : non|524 : non|
|950000|540 : oui|503 : non|524 : non|
|950180|561 : oui|533 : non|549 : **oui**|

Le seuil de cash intervient causalement dans cette décision. Mais le dernier contre-test apporte une limite importante : retirer le gain propre initial ne suffit pas à supprimer l'achat sur950180. On ne peut donc pas attribuer uniformément les trois trajectoires au seul gain du pas120. L'historique des instances est conservé, mais le cash est artificiellement modifié au pas132 : ce test n'est pas le résultat d'une trajectoire contrefactuelle complète.

Sur950080 et950000, les actions d'unités divergent ensuite au pas149 ; à la fin de ce pas, le candidat a8 ouvriers et le parent9. Sur950180, la première divergence d'actions d'unités est au pas203. Ces observations motivent une étude des réservations financières et du travail disponible ; elles ne prouvent pas qu'interdire l'achat anticipé ferait gagner.

## Flux réellement exécutés

Les écarts suivants sont des recettes réalisées, pas une valorisation de commandes proposées. Quantités vendues et prix moyens diffèrent : ne pas attribuer l'intégralité de l'écart à un prix défavorable.

| Graine, siège0 | Produit | Unités candidat / parent | Recettes candidat / parent | Différence |
|---|---|---:|---:|---:|
|950080|MILK|171 /207|33510 /40507|−6997|
|950080|STRAWBERRY|239 /274|33966 /34969|−1003|
|950000|STRAWBERRY|267 /294|54110 /57492|−3382|
|950180|STRAWBERRY|294 /314|55758 /59254|−3496|

Les autres produits et dépenses compensent une partie de ces écarts. Les totaux de toutes les transactions, une sélection de transactions localisées et la réconciliation exacte se trouvent dans `results/diagnose-sale-pressure-analysis.json`. Aucun stock terminal marchand n'explique les déficits sélectionnés.

## Hypothèses et prochain choix

- H1, premier tri défavorable : REFUTED sur les trois tours120 testés ; rôle des tris suivants UNRESOLVED.
- H2a, asymétrie initiale/de siège seule : WEAKENED par les trois contrôles parent-self égaux et les pertes identiques aux deux sièges.
- H2b, sensibilité d'achat au cash : SUPPORTED pour la décision132 dans les trois cas ; lien avec le seul gain initial limité par le contre-exemple950180.
- H2c, ces achats expliquent les défaites terminales : UNRESOLVED. Aucun achat n'a été supprimé dans une politique rejouée jusqu'au terme.

Priorité proposée : examiner la réservation de trésorerie pour les ouvriers et les besoins alimentaires avant investissement animal. Trois questions guident le prochain design : quel travail additionnel est réellement disponible, quelles dépenses proches doivent être réservées, et quel horizon de recettes finance l'investissement ? Une correction, si approuvée, devra être générale, isolée et mesurée sur de nouvelles graines ; aucun seuil ajusté aux trois cas ci-dessus.

## Reproduction

Python3.12.14, bibliothèque standard, depuis la racine. Les destinations doivent être neuves. Ne pas appeler le replay sans préciser le candidat et la campagne : ses valeurs par défaut concernent CARE.

```bash
python -m evaluation.replay --candidate candidates/k_pro6_sale_pressure.py \
  --opponent k_pro/k_pro6.py --campaign-b results/sale-pressure-b \
  --seed 950080 --seed 950000 --seed 950180 \
  --output /tmp/diagnose-sale-pressure-new
```

Contrôles parent-self (trois autres parties, pas de nouvelles observations de B) :

```bash
python - <<'PY'
import json
from pathlib import Path
from evaluation.campaign import run_match, _atomic_bytes
from evaluation.replay import replay_match, write_replay
out = Path('/tmp/diagnose-sale-controls-new'); out.mkdir(exist_ok=False)
records = []
for seed in (950080, 950000, 950180):
    job = dict(candidate='k_pro/k_pro6.py', opponent='k_pro/k_pro6.py', seed=seed, seat=0)
    row = run_match(job); trace = replay_match(job, row['scores'])
    name = f'seed-{seed}.jsonl.gz'; write_replay(out / name, trace)
    records.append(dict(file=name, job=job, scores=row['scores'],
                        label='parent-self diagnostic, not campaign B'))
_atomic_bytes(out / 'summary.json', (json.dumps(dict(diagnostic_only=True, matches=records), indent=2)+'\n').encode())
PY
python -m evaluation.diagnose /tmp/diagnose-sale-pressure-new/*.jsonl.gz \
  /tmp/diagnose-sale-controls-new/*.jsonl.gz --output /tmp/diagnose-sale-analysis-new.json
```

Contre-tests à partir des traces publiées, en lecture seule :

```bash
python - <<'PY'
import copy, gzip, json
from pathlib import Path
from evaluation.engine import ROOT, load_policy, offline_policy
from evaluation.diagnose import analyze_order_swap
for seed in (950080, 950000, 950180):
    path = Path(f'results/diagnose-sale-pressure/seed-{seed}-seat-0.jsonl.gz')
    records = [json.loads(x) for x in gzip.decompress(path.read_bytes()).splitlines()]
    rows = records[1:-1]
    swap = analyze_order_swap(path, 0, 120, (0, 1)); print('swap', seed, swap)
    for mode in ('rival_cash', 'cancel_own_gain'):
        policies = [load_policy(ROOT/'candidates/k_pro6_sale_pressure.py') for _ in range(2)]
        for t in range(133):
            actions = []
            for i, policy in enumerate(policies):
                obs = copy.deepcopy(rows[t]['pre'][0])
                if t == 132 and i:
                    if mode == 'rival_cash':
                        obs['farms'][0]['money'] = obs['farms'][1]['money']
                    else:
                        obs['farms'][0]['money'] += swap['money_effect'][0]
                with offline_policy():
                    actions.append(policy(obs, copy.deepcopy(records[0]['configuration'])))
            assert actions[0] == rows[t]['actions'][0]
            if t < 132: assert actions[1] == actions[0]
        print(seed, mode, actions)
PY
```

Preuves : neuf traces gzip et leurs deux résumés, l'analyse des commits économiques, `results/diagnose-sale-pressure-countertests.json` et `results/diagnose-sale-pressure-gain-cancelled.json`. Les sources restent identiques à celles de leur génération ; les traces peuvent contenir les informations privées des deux fermes uniquement pour le diagnostic hors agent. Rien n'est injecté dans la politique en compétition.
