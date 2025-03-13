import requests
import pandas as pd
from collections import defaultdict

# IDs de tickets à interroger (de 500 à 700)
ticket_ids = [639, 641,642,656,671,676,677,682,683,692,694,695,697,698,699]
url_template = "https://service-desk.focus-corporation.com/api/v3/changes/{}"
headers = {"authtoken": "906B26D6-70E5-4B71-BAF8-DCD21143B0EE"}

# Dictionnaires pour stocker les utilisateurs par statut et par ID de ticket
reviewers_by_status_and_ticket = defaultdict(lambda: defaultdict(list))
implementers_by_status_and_ticket = defaultdict(lambda: defaultdict(list))

# Boucle à travers chaque ID de ticket
for ticket_id in ticket_ids:
    url = url_template.format(ticket_id)
    response = requests.get(url, headers=headers, verify=False)

    # Vérifiez le code d'état de la réponse
    if response.status_code == 200:
        ticket_data = response.json()
        change_info = ticket_data.get('change', {})

        # Récupération de l'état du ticket
        ticket_status = change_info.get('status', {}).get('name', 'Inconnu')

        # Récupération des reviewers et implementers
        for role in change_info.get('roles', []):
            user_info = role.get('user', {})
            if role.get('role', {}).get('internal_name') == 'Reviewer':
                reviewers_by_status_and_ticket[ticket_status][ticket_id].append({
                    'name': user_info.get('name'),
                    'email': user_info.get('email_id'),
                    'mobile': user_info.get('mobile'),
                })
            elif role.get('role', {}).get('internal_name') == 'Implementer':
                implementers_by_status_and_ticket[ticket_status][ticket_id].append({
                    'name': user_info.get('name'),
                    'email': user_info.get('email_id'),
                    'mobile': user_info.get('mobile'),
                })
    else:
        print(f"Erreur lors de la récupération des données pour le ticket ID {ticket_id}: {response.status_code}")

# Préparation des données pour l'exportation
data = {
    'Statut': [],
    'Type': [],
    'Ticket ID': [],
    'Nom': [],
    'Email': [],
    'Mobile': [],
}

# Ajout des reviewers aux données
for status, tickets in reviewers_by_status_and_ticket.items():
    for ticket_id, reviewers in tickets.items():
        for reviewer in reviewers:
            data['Statut'].append(status)
            data['Type'].append('Reviewer')
            data['Ticket ID'].append(ticket_id)
            data['Nom'].append(reviewer['name'])
            data['Email'].append(reviewer['email'])
            data['Mobile'].append(reviewer['mobile'])

# Ajout des implementers aux données
for status, tickets in implementers_by_status_and_ticket.items():
    for ticket_id, implementers in tickets.items():
        for implementer in implementers:
            data['Statut'].append(status)
            data['Type'].append('Implementer')
            data['Ticket ID'].append(ticket_id)
            data['Nom'].append(implementer['name'])
            data['Email'].append(implementer['email'])
            data['Mobile'].append(implementer['mobile'])

# Création d'un DataFrame pandas
df = pd.DataFrame(data)

# Sauvegarde du fichier Excel
excel_file_path = "C:\\Users\\uid1945\\Desktop\\reviewers_implementers_report.xlsx"  # Chemin mis à jour
df.to_excel(excel_file_path, index=False)

print(f"Le rapport a été enregistré dans le fichier : {excel_file_path}")
