import requests
from fuzzywuzzy import fuzz

# URL et headers de l'API pour récupérer les tickets
url = "/api/v3/requests"
headers = {"authtoken": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"}
input_data = '''{
    "list_info": {
        "row_count": 1,
        "start_index": 1
    }
}'''
params = {'input_data': input_data}

# Liste des mots-clés pour détecter l'incident cloud
cloud_keywords = [
    "connectivité", "vpn", "serveur", "réseau", "sauvegarde", "authentification", "virtualisation", 
    "vm", "vcenter", "vcloud director", "accès distant", "sécurité", "firewall", "base de données", 
    "réplication", "backup", "accès", "certificat", "gestion des identités", "création de comptes", 
    "suppression de comptes", "gestion des accès", "vrops", "vcloud", "veeam", "connexion", "cluster", 
    "mot de passe", "performance", "rdp", "qlik"
]

# Fonction pour détecter le type d'incident avec traitement des erreurs
def detect_incident_type(ticket):
    subject = ticket['subject'].lower()
    short_description = ticket['short_description'].lower()
    combined_text = subject + " " + short_description

    # Vérifier les mots-clés cloud en utilisant fuzzywuzzy pour la correspondance approximative
    for keyword in cloud_keywords:
        for word in combined_text.split():
            if fuzz.ratio(keyword.lower(), word) > 80:  # Si le mot correspond à plus de 80% au mot-clé
                return "Incident Cloud"
    
    # Si aucun mot-clé cloud n'est trouvé, classer l'incident comme "Incident Infrastructure"
    return "Incident Infrastructure"

# Fonction pour mettre à jour le ticket avec le type d'incident
def update_ticket(ticket_id, incident_type):
    url_update = f"/api/v3/requests/{ticket_id}"
    input_data_update = f'''{{
        "request": {{
            "udf_fields": {{
                "udf_pick_5401": "{incident_type}"
            }}
        }}
    }}'''
    data = {'input_data': input_data_update}
    response = requests.put(url_update, headers=headers, data=data, verify=False)
    return response.status_code, response.text

# Récupérer les tickets via l'API
response = requests.get(url, headers=headers, params=params, verify=False)

# Si la requête est réussie, traiter les tickets
if response.status_code == 200:
    tickets = response.json().get("requests", [])
    for ticket in tickets:
        ticket_id = ticket.get("id")
        incident_type = detect_incident_type(ticket)
        print(f"Ticket ID: {ticket_id} - Type: {incident_type}")

        # Mettre à jour le ticket avec le type d'incident
        status_code, response_text = update_ticket(ticket_id, incident_type)
        print(f"Update Status for Ticket ID {ticket_id}: {status_code} - {response_text}")

else:
    print("Erreur lors de la récupération des tickets")
