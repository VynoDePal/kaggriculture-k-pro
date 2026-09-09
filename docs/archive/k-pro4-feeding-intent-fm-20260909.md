> Archive technique éditée pour cette publication. Ce document n’est pas un rapport de performance ni un statut actuel de livraison.

## 1. Cause observée : achats sans tenir compte du jeûne voulu

FL compte correctement le stock physique, mais conserve le besoin historique de tous les animaux non nourris : 18 + 6 − 17 = 7 blés à acheter. FM utilise l'intention de nourrissage existante, sans inventer un jeûne supplémentaire : 15 + 6 − 17 = **4 blés**. La phase officielle confirme 21 blés après les transactions, soit 15 rations et 6 de réserve.

La réserve n'est jamais inférieure au tiers du troupeau planifié **ni au nombre d'animaux volontairement à jeun**, afin de réserver au moins leur prochaine ration. Un animal ayant déjà manqué un nourrissage reste compté comme à nourrir, même si une future modification du générateur de tâches devait omettre FEED.

## 2. Contrat de la correction locale

`feeding_intent_fm.py` est installé après FL dans la chaîne expérimentale FI/FJ2/FK/FL/FM.

Il s'agit d'une correction de cohérence du budget alimentaire, pas d'une nouvelle politique animale complète. La réserve physique ne prouve pas la faisabilité des tournées du lendemain ; elle ne garantit pas non plus que différer l'achat sera financièrement favorable à des prix futurs inconnus.

## 3. Tests et intégration

Trois tests rouges initiaux ont reproduit l'achat trop élevé, le besoin de conserver la réserve lorsque tous les animaux jeûnent et la réservation des ventes. Après implémentation : tests verts. Dix tests FM couvrent aussi prix redevenu élevé, animal déjà affamé, jours terminaux, achats multiples, achat initial déjà inférieur au plafond, non-mutation et intégration sur le tour suivant.

Le test de deux décisions conserve le véritable état issu de la phase corrigée du pas337. Sans changement d'intention, l'achat supprimé n'est pas recréé au pas338. Avec un choc contrôlé du prix de la laine à200, la politique redevient nourrissante et l'achat nécessaire de3blés réapparaît : aucune exemption de nourriture mémorisée à tort.

Suite ciblée finale : **125 tests réussis en 8,29 s**, sortie 0. Couvre logistique, projection, journaux et FI/FJ2/FK/FL/FM ; ne constitue pas une suite globale de toutes les anciennes expériences.

## 5. Maturation des melons : expérience, pas activation

Résultats :

- Même récolte de6melons et même première date biologique J10 dans les63cas.
- Une action locale économisée dans54cas ; aucune dans9cas.
- Une unité d'engrais consommée dans chaque variante, cotée81à92 au moment de l'observation. Ce cours est un coût d'opportunité indicatif, pas une vente garantie.
- Dans le cas de service sur place, le dernier arrosage deJ10 est évité, mais un retour et une vente plus précoces dans la ferme réelle ne sont pas démontrés.

Ces essais ne sont pas cumulables : plusieurs situations peuvent réutiliser le même engrais enregistré et aucun coût des autres tâches déplacées n'est encore calculé. La fertilisation des melons reste donc **non activée**, faute de preuve que le service gagné et le calendrier de vente compensent l'engrais et les autres emplois possibles.

## 6. Suite et limites

L'allègement deJ10 exige encore un arbitrage financé entre ravitaillement, élevage, première récolte, deuxième vague et livraison. La piste d'engrais ne remplace pas ce chantier. Prochaine étape : vérifier des créneaux de service et de livraison conjointement avec leurs tâches concurrentes, plutôt qu'un bonus de priorité arbitraire.

## Provenance

Tous les processus de cette étape ont terminé. Aucun effacement ; dernier relevé603Mo libres sur le disque système et121Go surDePal. L'espace système reste à surveiller.
