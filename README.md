# Kaggriculture — Série K Pro

Sources Python et documentation technique de la série K Pro.

Ce dépôt indépendant est un instantané du travail au 9 septembre 2026.
Il ne reprend pas l’historique Git du projet d’origine. Les sources Python
archivées sont conservées à l’identique ; leurs empreintes figurent dans
`SOURCE_HASHES.json`. Les documents historiques sont des éditions techniques
abrégées : le présent README décrit l’état des versions.

## Versions autonomes

| Version | Fichier | État |
|---|---|---|
| K Pro 1 | `k_pro/k_pro1.py` | Version historique autonome |
| K Pro 2 | `k_pro/k_pro2.py` | Version historique autonome |
| K Pro 3 | `k_pro/k_pro3.py` | Version historique autonome |
| K Pro 4 | `k_pro/k_pro4_loader_fixed.py` | Point d’entrée corrigé |
| K Pro 5 | `k_pro/pro5/` | Travaux expérimentaux, pas de fichier final unique |
| K Pro 6 | `k_pro/k_pro6.py` | Dernière version autonome livrée |

**Attention :** `k_pro/k_pro4.py` est conservé comme archive de développement.
Utiliser `k_pro4_loader_fixed.py` pour cette version.
`k_pro/agent.py`, les dossiers `experiments/`, `pro2/` à `pro5/` et `research/`
contiennent des prototypes : leur présence ne signifie pas qu’ils sont prêts
à être livrés ni qu’ils sont intégrés à K Pro 6.

## Architecture

La politique construit un plan de cultures et d’élevage, génère les tâches par
case, affecte les ouvriers, réserve les ressources et prépare les opérations
de marché. Les décisions utilisent les observations disponibles et les stocks
propres. Les fichiers autonomes utilisent la bibliothèque standard Python.

K Pro 6 regroupe les corrections de récolte de secours, d’échéance des plantations,
de fertilisation locale, de comptabilité du blé et de réserve alimentaire.
Son entrée principale est `kaggle_agent(observation, configuration=None)`.

La configuration livrée n’active pas le quatrième quadrant. La planification
globale des revenus, des tournées et de l’expansion reste un travail en cours.
Aucune garantie d’optimalité générale n’est revendiquée.

## Organisation

- `k_pro/` : versions autonomes et archives de prototypes.
- `research/` : composants de recherche conservés séparément.
- `docs/architecture.md` : principes et limites de conception.
- `docs/corrections.md` : corrections intégrées et chantier suivant.
- `docs/archive/` : éditions techniques des notes Markdown historiques.
- `SOURCE_HASHES.json` : empreintes SHA-256 des fichiers Python importés.
- `tests/` : contrôles autonomes d’intégrité de cette publication.

Certains composants de recherche sont des bibliothèques expérimentales et
supposent les modules voisins présents dans leur dossier. Ils ne constituent
pas une application installable ni une suite de lancement complète.

## Vérification de l’archive

```bash
python -B -m unittest discover -s tests -v
```

Ce contrôle compile les sources sans les exécuter, vérifie leurs empreintes et
le chargement des cinq fichiers autonomes. Il ne mesure pas leur performance.
Le développement et les derniers contrôles détaillés ont utilisé Python 3.14.
L’équivalence numérique entre toutes les versions de Python n’est pas certifiée.

La série reste en développement. Les notes anciennes peuvent décrire des
tentatives non retenues ; elles ne changent pas l’état des versions ci-dessus.
