> Archive technique éditée pour cette publication. Ce document n’est pas un rapport de performance ni un statut actuel de livraison.

Travail en cours, non soumis, aucun incumbent remplacé. Demande utilisateur :
nouvelle architecture fondée sur les expériences, délai maximal de quatre heures.
Début de cette reprise vers 11:52 UTC ; échéance de travail visée 15:52 UTC.
Il est impossible de garantir un agent imbattable.

## Nouvelle architecture expérimentale

- modèle de prix et scénarios de demande publique ;
- allocation de capital et choix du cheptel/cultures/terrains ;
- contrats de travail observables par case ;
- affectation spatiale et ravitaillement des ouvriers ;
- livraison anticipée pour financer la croissance, gestion du marché ;
- dépôt et vente de fin de partie.

Les snapshots `k_pro/experiments/prototype_a.py` et `prototype_b.py` sont gelés
pour les expériences correspondantes. Le fichier principal reste de développement.

## Point intermédiaire — 13:18 UTC

**Toujours expérimental. Ni soumission, ni remplacement d'un agent existant.**
Le fichier `k_pro/agent.py` contient des options expérimentales dont plusieurs
régressent. Ce n'est PAS le livrable final. Les snapshots A à P restent inchangés.

Corrections identifiées et couvertes par tests (22 tests à ce stade) :

### Résultats comparables, banques de développement uniquement

Les affectations rigides par métier, le routage par insertion statique, les
retours systématiques des ouvriers libres, plusieurs plantations diamant 4Q
forcées, et les prévisions économiques plus complexes ont souvent régressé.
Ces branches sont conservées comme expériences rejetées, pas intégrées par défaut.

## Point intermédiaire — 13:56 UTC

Les 15 hashes de la campagne C/50 lait/alimentation ont été revérifiés : tous
inchangés. Les tests de performance restent uniquement CPU, avec pools bornés ;
les campagnes indépendantes utilisent au plus 16 workers simultanés, hors petits
contrôles de compatibilité. Aucune source antérieure verrouillée n'est modifiée.

## Point intermédiaire — 14:35 UTC

Autres contrôles achevés :

### Sélection figée à 14:57 UTC

Les finalistes comparés sur les mêmes 1 400 clés C/50 donnent :

### Compatibilité et limites

Précision issue de la lecture du compteur natif : `produced` compte les unités
récoltées/collectées, pas la production encore au champ ni les ventes. `discarded`
compte les pertes au dépôt, pas les fuites d'animaux. Les tableaux descriptifs du
rapport final emploient cette terminologie précise.
