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
  --output results/measure-care-a
```

2400 matchs,200 seeds uniques. Les paires partagent leur banque, donc leurs résultats ne sont pas indépendants. La banque B930000–930199 est réservée à une confirmation sans retouche, conditionnée par le protocole pré-enregistré dans `docs/plans/2026-09-09-measure-care.md`.

## Artefacts et interprétation

- `manifest.json` : sources/moteur/config/seeds, version Python, statut et empreintes des résultats. Seul `COMPLETE` prouve l'achèvement ; `RUNNING` ou `FAILED` ne doit pas être résumé comme campagne complète.
- `matches.jsonl` : clé de chaque match, scores, marge, commandes émises, soins trop tardifs proposés, temps de décision et commerces finaux.
- `summary.json` : victoires, marges, sièges et IC95 calculés sur200 moyennes par seed (deux sièges), Student199.

Le calcul des IC est descriptif pour chaque paire. Ne pas choisir le meilleur résultat parmi plusieurs variantes puis le présenter comme une confirmation indépendante. Ne pas agréger plusieurs adversaires comme des observations indépendantes.

Le moteur résout719 décisions et720 états, initial compris. Le seed est retiré de la configuration visible. Chaque match utilise un nouveau processus ; les imports du chargement sont restaurés et les observations/configurations sont copiées. Une action de forme invalide, une mutation ou un résultat absent/dupliqué fait échouer l'évaluation. Les emplacements de marché vides sont conservés : FL/FM les utilisent pour préserver les indices de résolution simultanée. Les résultats écrits sont relus et validés avant COMPLETE. Les commandes comptées ne sont pas toutes des actions économiquement utiles ; les soins classés tardifs ne sont pas valorisés comme des pertes monétaires.

Le même seed ne fige pas les commerces lorsque les cases vides changent : le RNG des mauvaises herbes et du commerce journalier est partagé dans le moteur officiel. Les deux sièges et les diagnostics par trajectoire restent nécessaires.

## Limites

Le banc appelle l'interpréteur et le sélecteur de callable officiels, avec orchestration locale. Un hook d'audit Python interdit les sockets, requêtes HTTP, appels ctypes et processus externes pendant le chargement et les décisions. Il est destiné aux politiques K Pro autonomes de confiance : ce n'est pas une frontière de sécurité contre du code hostile. Le banc n'émule ni le sandbox ni les limites de temps/overage du framework distant. Il n'établit pas une parité intégrale avec tous les comportements du package `kaggle_environments`. Les temps de décision sous charge locale ne garantissent pas les délais sur Kaggle. Les sources officielles sont conservées exactement ; deux fonctions auxiliaires sont extraites par AST pour éviter les dépendances externes. Le pont moteur ne modifie pas `sys.modules` ; le chargeur restaure son état après les imports de politique.

Le panel interne K Pro contrôle les changements de la série ; il ne prouve pas la compétitivité contre les adversaires actuels du ladder. Les traces économiques et confrontations récentes constituent l'étape suivante du plan validé.
