> Archive technique éditée pour cette publication. Ce document n’est pas un rapport de performance ni un statut actuel de livraison.

## 2. Notre validation locale était trop favorable à une lecture globale

C'est une preuve sur ces trajectoires, pas une garantie universelle. Le fichier distant n'a pas été téléchargé : l'identité est étayée par le reçu, les métadonnées et la reproduction comportementale. Légalité des actions et rentabilité restent deux sujets différents.

## 4. Melons : produire n'est pas commercialiser au bon moment

Recommandation à tester : rentabilité marginale du troupeau et disponibilité future du blé, en incluant actions et valeur de revente. Ni nourrir systématiquement, ni cesser de nourrir dès qu'un prix baisse n'est justifié par ces seuls résultats.

## 6. Le dépôt nocturne fonctionne, mais le contrôle de capacité laisse perdre des biens

La fonction `idle_deliveries` décrit des livraisons préventives dans sa documentation, mais son corps ne fait que retourner les entrées. Elle est inactive dans le fichier soumis. Le marché considère une projection du stock porté, sans pouvoir vendre directement ces objets tant qu'ils ne sont pas déposés.

## 7. Le profil soumis ne réalise pas le diamant complet à quatre quadrants

Les 21 trajectoires examinées pour la géométrie ont trois quadrants à J29. Plus fondamentalement, la condition d'achat est :

`q < 4 and (q < 3 or False)`

Quand trois quadrants sont ouverts, cette condition est fausse. Le quatrième quadrant est donc désactivé, pas simplement rarement déclenché. Il ne faut pas présenter K Pro 3 comme la réalisation de la stratégie diamant complète envisagée ensemble.

Cela ne prouve pas que forcer le quatrième ferait gagner : son terrain, son travail et son capital doivent être rentabilisés. Cela prouve qu'il faut distinguer explicitement le profil testé de l'architecture demandée.

## 8. Pourquoi nous gagnons quand même

Nos carottes, fraises, laine, diversification et économies de main-d'œuvre peuvent compenser ces handicaps :
