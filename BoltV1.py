import requests
import pandas as pd
import re
import json

# Charger le fichier Excel
file_path = "Transport.xlsx"
data = pd.read_excel(file_path)

# URL et headers de l'API
request_url_template = "https://service-desk.focus-corporation.com/api/v3/requests/{request_id}/worklogs"
change_url_template = "https://service-desk.focus-corporation.com/api/v3/changes/{change_id}/worklogs"
headers = {
    "authtoken": "906B26D6-70E5-4B71-BAF8-DCD21143B0EE",
    "accept": "application/vnd.manageengine.sdp.v3+json"
}

# Parcourir chaque ligne du fichier Excel
for index, row in data.iterrows():
    raison_du_trajet = str(row["Raison du trajet"])
    prix_tva = row["Prix avec TVA"]
    utilisateur = row["Nom d’utilisateur"]
    duree_minutes = row["Durée en minutes"]

    # Vérifier si la durée est valide (non NaN et positive)
    if pd.isna(duree_minutes) or duree_minutes < 0:
        print(f"Request ID non traité (ligne {index + 1}): Durée invalide.")  # +1 pour afficher la ligne correcte
        continue  # Passer à la ligne suivante si la durée est invalide

    # Concaténer les colonnes A, B, C, D, et E pour la description
    description = f"{row['Date']} - De: {row['De']} À: {row['À']} - Destination: {row['Destinations']} - Durée: {duree_minutes} minutes"

    # Calcul des heures et minutes
    hours = duree_minutes // 60  # Division entière
    minutes = duree_minutes % 60   # Reste de la division

    # Rechercher le request ID (5 chiffres) et le change ID (3 chiffres) sans les lettres
    request_match = re.search(r'\b(\d{5})\b', raison_du_trajet)  # 5 chiffres
    change_match = re.search(r'\b(\d{3})\b', raison_du_trajet)   # 3 chiffres

    if request_match:
        request_id = request_match.group(0)
        print(f"Request ID trouvé (ligne {index + 1}): {request_id}")  # +1 pour afficher la ligne correcte
        url = request_url_template.format(request_id=request_id)
    elif change_match:
        change_id = change_match.group(0)
        print(f"Change ID trouvé (ligne {index + 1}): {change_id}")  # +1 pour afficher la ligne correcte
        url = change_url_template.format(change_id=change_id)
    else:
        # Rechercher les 3 chiffres dans la colonne "Raison du trajet" sans tenir compte des lettres
        all_matches = re.findall(r'\d{3}|\d{5}', raison_du_trajet)
        if all_matches:
            for match in all_matches:
                if len(match) == 5:
                    request_id = match
                    print(f"Request ID trouvé dans les correspondances (ligne {index + 1}): {request_id}")  # +1 pour afficher la ligne correcte
                    url = request_url_template.format(request_id=request_id)
                    break
                elif len(match) == 3:
                    change_id = match
                    print(f"Change ID trouvé dans les correspondances (ligne {index + 1}): {change_id}")  # +1 pour afficher la ligne correcte
                    url = change_url_template.format(change_id=change_id)
                    break
        else:
            print(f"ID non trouvé (ligne {index + 1}): {raison_du_trajet}")  # +1 pour afficher la ligne correcte
            continue  # Passer à la ligne suivante si aucun ID trouvé

    # Structurer les données pour inclure "input_data" comme chaîne de caractères
    input_data = {
        "worklog": {
            "owner": {
                "name": utilisateur
            },
            "other_cost": str(prix_tva),
            "type": {
                "name": "Transport"
            },
            "description": description,
            "time_spent": {
               "hours":  0, #int(hours),   # Convertir en int
              "minutes": 0 #int(minutes)
            }
        }
    }

    # Envoi de la requête à l'API
    data = {'input_data': json.dumps(input_data)}
    response = requests.post(url, headers=headers, data=data, verify=False)

    # Afficher la réponse
    print(f"Input Data pour ID {request_id if 'request_id' in locals() else change_id}: {json.dumps(input_data, indent=4)}")
    print(f"Réponse de l'API: {response.text}")
