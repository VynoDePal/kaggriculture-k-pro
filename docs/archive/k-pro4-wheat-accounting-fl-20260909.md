> Archive technique éditée pour cette publication. Ce document n’est pas un rapport de performance ni un statut actuel de livraison.

## Statut et périmètre

La demande précédente de bilan a été satisfaite en lecture seule. Cette continuation ajoute une vérification fraîche de la suite ciblée, deux nouvelles pertes réelles et un diagnostic du calendrier de production. L'objectif complet reste ouvert.

## Cause et correction FL

Le planificateur soustrait le blé ramassé par les ouvriers du hangar virtuel, mais la politique d'achat additionne encore les inventaires des mains **avant** leur ramassage. Du blé toujours possédé disparaît ainsi du calcul de réserve et peut être racheté inutilement. Une récolte ou un nourrissage peut également rendre cette photographie périmée.

`wheat_accounting_fl.py` projette les actions propres dans leur ordre canonique, puis compte le blé dans le hangar et dans les mains, ainsi que les animaux restant non nourris. Il conserve la réserve prévue par la référence : animaux non nourris plus un tiers du troupeau planifié. Toutes les ventes de blé proposées sont réservées avant de réduire l'achat.

- Ne peut que réduire l'unique achat de blé existant, jamais l'augmenter.
- Ne change ni tâche, ni cible, ni mémoire, ni autre ordre de marché.
- Un achat annulé devient un emplacement vide ignoré par le parseur officiel : les indices simultanés des commandes suivantes ne se décalent pas.
- Si plusieurs achats de blé sont proposés, aucun changement : le succès d'un achat antérieur n'est pas supposé.
- Les jours 28 et 29 conservent la politique terminale originale.
- La projection globale du marché reste désactivée ; sa réactivation antérieure avait régressé stratégiquement.

La réserve demeure une heuristique : elle ne garantit pas qu'un ouvrier pourra physiquement acheminer chaque unité à un animal au moment voulu. FL ne résout ni les ventes excessives, ni l'autonomie agricole, ni le jeûne économique.

## Validation ciblée

Ces sommes ne sont ni des économies réalisées sur une trajectoire corrigée ni du score gagné : chaque phase repart de l'ancien état enregistré. En particulier, il serait faux d'additionner les montants conservés et de les ajouter au score Kaggle.

## Deux pertes téléchargées après fixation des correctifs

La référence reproduit exactement les 1 438 actions enregistrées ; les journaux réconcilient les transactions. FI/FJ2/FK/FL gardent leurs empreintes précédentes. L'audit indépendant des phases unités correspond au moteur officiel ; aucune plantation surconsommant les graines. FJ2 élimine les 26 et 24 affectations hors délai observées, sans suppression des actions de référence WATER/FEED/CARE/FERTILIZE dans ces séquences. FL ne change aucun autre ordre d'unité ni autre transaction propre exécutée. FI n'ajoute aucune récolte sur ces deux cas.

### Prochaine expérience à spécifier

Décomposer les journées de récolte de la première vague : tâches fixes de ravitaillement, services animaux, plantations de la seconde vague et livraisons. Identifier un conflit concret de calendrier puis construire un test contrôlé qui compte tous les services déplacés, la capacité et le financement. Ne pas remplacer ce chantier par un simple bonus de priorité ou par un ajout de melons non financé.
