> Archive technique éditée pour cette publication. Ce document n’est pas un rapport de performance ni un statut actuel de livraison.

## Conclusion

Le diagnostic indépendant, puis la lecture directe du journal noyau par le contrôleur, identifient un BUG du chemin d'écriture NTFS3, et non une faute démontrée de l'agent ou du simulateur. Aucun correctif de politique n'est justifié par cet incident.

## Preuves

Ressources vérifiées après incident : environ 829 MiB libres sur le système, 136 GiB sur l'externe, 9 GiB de RAM disponible. Les seuils de garde n'ont pas causé cet arrêt. La baisse récente d'espace système reste inexpliquée ; aucun core récent enregistré n'a été trouvé par la revue. Aucune donnée personnelle supprimée.

## Garde de reprise

Ne lancer aucun calcul ni aucune écriture expérimentale sur DePal dans ce boot après ce BUG. Ne pas redémarrer ou réparer le système sans coordination utilisateur. Demander un redémarrage du PC, puis revérifier le noyau, le montage et l'intégrité du stockage : un redémarrage seul ne démontre pas que le défaut NTFS3 est corrigé. Si le chemin reste incertain, maintenir l'arrêt et proposer une récupération séparée ; ne pas déplacer silencieusement les capsules ou contourner le manifeste.

Une éventuelle reprise doit préserver les sources/configurations/banques/capsules exactes, confirmer l'absence de processus et de résultat terminal, vérifier à nouveau toutes les cellules et ne traiter que le suffixe canonique manquant avec le runner gelé et 8 workers. Ne rejouer ni N, ni O, ni les 480 cellules P. La fin absolue reste le 8 septembre à 16:55:39 UTC ; les interruptions ne prolongent pas les 24 heures. Si le temps manque, P reste honnêtement incomplet et le final100 ne peut pas être déclaré effectué.

## Récupération autorisée et validée — 11:06–11:14 UTC

L'utilisateur a explicitement autorisé le remontage NTFS-3G et la reprise après vérification. Aucun utilisateur actif du volume selon fuser. Démontage propre via UDisks, sans force. La première demande du nom de type `ntfs-3g` a été refusée par UDisks sans monter le disque ; le nom autorisé `ntfs` appelle bien `/sbin/mount.ntfs`, lien vers NTFS-3G. Aucun contournement d'authentification : sudo non interactif indisponible, montage utilisateur UDisks autorisé.
