# Automatisation ServiceDesk Plus

## Description
Ce projet regroupe plusieurs scripts Python développés pour automatiser des tâches récurrentes dans ServiceDesk Plus, notamment la gestion des tickets, des contrats et des actifs. Ces scripts permettent d'améliorer l'efficacité et de réduire l'intervention manuelle.

## Table des Matières
- [Installation](#installation)
- [Scripts Disponibles](#scripts-disponibles)
- [Utilisation](#utilisation)
- [Configuration](#configuration)
- [Recommandations](#recommandations)
- [Auteurs](#auteurs)

## Installation
1. **Cloner le dépôt** :
   ```sh
   git clone https://github.com/votre-repo.git
   cd votre-repo
   ```
2. **Installer les dépendances** :
   ```sh
   pip install -r requirements.txt
   ```
3. **Configurer les variables d'environnement** (voir [Configuration](#configuration)).

## Scripts Disponibles
### Gestion des Rapports et Facturation
- **FACTURE.py** : Génère un fichier Excel listant les contrats et les actifs associés.
- **Mardi_Rapport.py** : Génère un rapport Excel chaque mardi avec les tickets de changement non clôturés.

### Gestion des Tickets
- **détailRequest.py** : Met à jour le nom du contrat dans un ticket en fonction de l'actif.
- **MPVfinal.py** : Met à jour l’objet du ticket en fonction du contrat et de la fréquence de maintenance.
- **fiche.py** : Vérifie la présence d’une fiche d’intervention avant clôture d’un ticket.
- **description.py** : Met à jour les champs d’un ticket après une sortie de pièce de rechange.
- **BoltV1.py** : Enregistre les trajets et coûts des techniciens dans les worklogs des tickets.

### Gestion des Contrats
- **PopUpStatutDuContra.py** : Met à jour le statut des contrats (actif ou expiré).
- **SignatureDuPvDéfinitif.py** : Envoie un mail 15 jours avant expiration d’un contrat.
- **Rappel_SMS_6mois.py** : Rappel automatique à la logistique pour renouvellement d’abonnement SMS.

### Gestion des Actifs
- **CodeFlare.py** : Met à jour la version d’un actif après clôture d’un ticket d’upgrade.

### Gestion des Heures de Travail
- **HJ.py** : Suit et met à jour la consommation des heures dans les contrats.

### Affectation Automatique des Tickets
- **NIV1-INFRA.py, NIV1-CLOUD.py, NIV2-INFRA.py, ASTREINTE.py** : IA pour assigner automatiquement les tickets en fonction des compétences requises et des disponibilités.

## Utilisation
Chaque script peut être exécuté indépendamment. Exemple :
```sh
python FACTURE.py
```
Certains scripts sont conçus pour être exécutés périodiquement via une tâche planifiée.

## Configuration
- Les informations sensibles (ex: identifiants API) doivent être stockées dans un fichier `.env`.
- Exemple de `.env` :
  ```ini
  SDP_API_KEY=your_api_key
  SDP_URL=https://your-servicedesk-url.com
  ```

## Recommandations
- Vérifier régulièrement les logs pour détecter d'éventuelles erreurs.
- Ne pas modifier directement les scripts en production sans test préalable.
- Planifier l'exécution des scripts avec `cron` (Linux) ou le Planificateur de tâches Windows.

## Auteurs
- **Mohamed Khalil El Mouedhen / Consultant IT**
- Contact : khalil.mouedhen@gmail.com

---
Ce projet est en constante évolution. N'hésitez pas à contribuer ou à signaler des améliorations ! 🚀
