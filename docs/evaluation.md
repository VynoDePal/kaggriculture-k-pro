# Évaluation reproductible K Pro

Ce banc utilise hors réseau les sources officielles figées dans `vendor/kaggriculture/` (licence Apache-2.0 et provenance incluses). Il n'installe pas les dépendances des autres jeux Kaggle. Python3.12 est la version mesurée ; le runner et les tests utilisent la bibliothèque standard.

## Vérification

Depuis la racine du dépôt :

```bash
python -B -m unittest discover -s tests -v
```

Les témoins `k_pro/k_pro2.py`, `k_pro/k_pro4_loader_fixed.py`, `k_pro/k_pro6.py` et leur manifeste d'archive restent inchangés. `k_pro/k_pro4.py` est un témoin d'incident de chargement, jamais un adversaire de performance.

## Candidat CARE

`candidates/k_pro6_care_fp.py` est expérimental. Il applique exclusivement l'adaptateur archivé FP à K Pro6. Une suppression de soins sans effet avant la fin n'est pas une preuve de gain terminal.

Pour reproduire le fichier sans écraser un artefact existant :

```bash
python -m evaluation.build_candidate /tmp/k_pro6_care_fp_rebuilt.py
```

## Campagne A figée

Le runner exige200 seeds consécutifs et joue les deux sièges de chaque paire. Le dossier de sortie doit ne pas exister.

```bash
python -m evaluation.campaign --seed-start 920000 --workers 8 \
  --pair k_pro/k_pro4_loader_fixed.py k_pro/k_pro2.py \
  --pair k_pro/k_pro6.py k_pro/k_pro2.py \
  --pair k_pro/k_pro6.py k_pro/k_pro4_loader_fixed.py \
  --pair candidates/k_pro6_care_fp.py k_pro/k_pro6.py \
  --pair candidates/k_pro6_care_fp.py k_pro/k_pro4_loader_fixed.py \
  --pair candidates/k_pro6_care_fp.py k_pro/k_pro2.py \
  --output results/measure-care-a-durable
```

2400 matchs,200 seeds uniques. Les paires partagent leur banque, donc leurs résultats ne sont pas indépendants. La banque B930000–930199 est réservée à une confirmation sans retouche, conditionnée par le protocole pré-enregistré dans `docs/plans/2026-09-09-measure-care.md`.

## Artefacts et interprétation

- `manifest.json` : sources/moteur/config/seeds, version Python, statut et empreintes des résultats. Seul `COMPLETE` prouve l'achèvement ; `RUNNING` ou `FAILED` ne doit pas être résumé comme campagne complète.
- `matches.jsonl` : clé de chaque match, scores, marge, commandes émises, soins trop tardifs proposés, temps de décision et commerces finaux. Dans Git, ce fichier est conservé sans perte sous `matches.jsonl.gz` ; la sortie locale du runner reste du JSONL.
- `summary.json` : victoires, marges, sièges et IC95 calculés sur200 moyennes par seed (deux sièges), Student199.

Pour lire les résultats publiés sans extraction :

```python
import gzip, hashlib, json
from pathlib import Path
folder = Path("results/measure-care-a-durable")
raw = gzip.decompress((folder / "matches.jsonl.gz").read_bytes())
manifest = json.loads((folder / "manifest.json").read_text())
assert hashlib.sha256(raw).hexdigest() == manifest["results_sha256"]
rows = [json.loads(line) for line in raw.splitlines()]
```

Le calcul des IC est descriptif pour chaque paire. Ne pas choisir le meilleur résultat parmi plusieurs variantes puis le présenter comme une confirmation indépendante. Ne pas agréger plusieurs adversaires comme des observations indépendantes.

Le moteur résout719 décisions et720 états, initial compris. Le seed est retiré de la configuration visible. Chaque match utilise un nouveau processus ; les imports du chargement sont restaurés et les observations/configurations sont copiées. Une action de forme invalide, une mutation ou un résultat absent/dupliqué fait échouer l'évaluation. Les emplacements de marché vides sont conservés : FL/FM les utilisent pour préserver les indices de résolution simultanée. Chaque résultat est publié dans un checkpoint fermé, atomique et accompagné d’un SHA256. Après relecture de tous les checkpoints, le JSONL complet est publié atomiquement sans écrasement, puis relu et validé avant COMPLETE. Le système de fichiers doit prendre en charge les liens physiques. Aucun fichier de résultat partiel n’est présenté comme complet. Les commandes comptées ne sont pas toutes des actions économiquement utiles ; les soins classés tardifs ne sont pas valorisés comme des pertes monétaires.

Le même seed ne fige pas les commerces lorsque les cases vides changent : le RNG des mauvaises herbes et du commerce journalier est partagé dans le moteur officiel. Les deux sièges et les diagnostics par trajectoire restent nécessaires.

## Replays économiques diagnostiques

Les six traces B publiées dans `results/diagnose-care-c/` se rejouent avec les
actions enregistrées. Le diagnostic entoure passivement les commits du moteur
officiel et vérifie chaque pré-état et post-état avant d'agréger les flux
réalisés. Il ne déduit pas de recette brute d'un delta net ou d'un prix coté.

```bash
python -m evaluation.diagnose results/diagnose-care-c/*.jsonl.gz \
  --output /tmp/diagnose-care.json \
  --swap-replay results/diagnose-care-c/seed-930053-seat-0.jsonl.gz \
  --swap-player 0 --swap-step 672 --swap-slots 1 2
```

La sortie est créée exclusivement et contient les SHA-256 des traces, les
agrégats de commits, la réconciliation du cash, les stocks terminaux et des
exemples localisés. Le swap optionnel exécute seulement l'étape indiquée avec
deux emplacements de marché échangés; ce n'est ni une politique ni un replay
complet contrefactuel.

`results/diagnose-care-controls-final/` contient trois parties K Pro6 contre
lui-même, une par graine et avec les deux fermes conservées. Elles sont
explicitement distinctes des six lignes B et servent seulement à exposer
l'asymétrie initiale/de siège.

## Limites

Le banc appelle l'interpréteur et le sélecteur de callable officiels, avec orchestration locale. Un hook d'audit Python interdit les sockets, requêtes HTTP, appels ctypes et processus externes pendant le chargement et les décisions. Il est destiné aux politiques K Pro autonomes de confiance : ce n'est pas une frontière de sécurité contre du code hostile. Le banc n'émule ni le sandbox ni les limites de temps/overage du framework distant. Il n'établit pas une parité intégrale avec tous les comportements du package `kaggle_environments`. Les temps de décision sous charge locale ne garantissent pas les délais sur Kaggle. Les sources officielles sont conservées exactement ; deux fonctions auxiliaires sont extraites par AST pour éviter les dépendances externes. Le pont moteur ne modifie pas `sys.modules` ; le chargeur restaure son état après les imports de politique.

Deux limites opérationnelles mineures restent ouvertes : après une exception de match, le pool peut finir des tâches déjà en file avant d’écrire FAILED ; une erreur de génération du candidat peut laisser un fichier de sortie vide. Relancer dans une nouvelle destination et ne consommer qu’un candidat reconstruit avec succès et vérifié. Ces limites ne changent pas les scores d’une campagne COMPLETE.

Le panel interne K Pro contrôle les changements de la série ; il ne prouve pas la compétitivité contre les adversaires actuels du ladder. Les traces économiques et confrontations récentes constituent l'étape suivante du plan validé.

## Incident d’écriture de la première tentative A

`results/measure-care-a/manifest.json` conserve le statut FAILED : les2400 résultats ont passé la validation en mémoire, mais seuls deux étaient visibles au chemin JSONL lors de la relecture. Aucun score de cette tentative n’est utilisé pour décider. Le mécanisme d’un fichier ouvert puis remplacé reproduit exactement ce symptôme ; l’origine du remplacement dans cet environnement reste non identifiée. Les sondes simples de concurrence ne l’ont pas reproduit spontanément.

Le correctif atomique a été validé, mais sa relance `measure-care-a-retry` a ensuite été interrompue par une réinitialisation de l’environnement après au moins1000 matchs calculés. La session a disparu et aucun fichier de résultats final n’avait été publié. Son manifeste RUNNING et un constat d’interruption sont conservés ; cette tentative ne fournit aucune estimation.

La tentative `measure-care-a-durable` utilise les mêmes graines, politiques et règles de décision, avec checkpoints par match et publication atomique finale. Les deux tentatives incomplètes restent distinctes. L’évolution du runner concerne la persistance ; aucune politique n’a été ajustée à partir d’un score partiel.

## Reprise après interruption

Sur une campagne incomplète créée avec le format de checkpoints actuel, relancer la même commande avec `--resume`. Il faut avoir constaté l’arrêt du processus précédent : ne jamais lancer deux écrivains sur le même dossier. Les graines, paires, version Python, workers, configuration et toutes les empreintes sources doivent être identiques. Un fichier altéré, un mauvais match ou une campagne COMPLETE sont refusés. Les résultats vérifiés ne sont pas rejoués ni écrasés ; les matchs manquants utilisent chacun un nouveau processus. Les anciens formats sans checkpoints ne sont pas repris.

Les checkpoints sont des fichiers locaux intermédiaires non versionnés. Le JSONL compressé publié contient tous les résultats, vérifiables avec le SHA256 du manifeste. Les petits fichiers temporaires restés après un arrêt brutal ne sont jamais considérés comme des résultats.
