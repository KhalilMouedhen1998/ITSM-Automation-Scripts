import requests
import warnings

# Ignorer les avertissements de sécurité pour des fins de test uniquement
warnings.simplefilter('ignore')

url_requests = "/api/v3/requests"
url_attachments = "/api/v3/requests/{ticket_id}/attachments"
url_update_udf = "/api/v3/requests/{request_id}"
headers = {"authtoken": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"}

# Fonction pour mettre à jour le champ UDF
def update_udf(request_id, subject, value):
    input_data = f'''{{
        "request": {{
            "udf_fields": {{
                "udf_pick_10803": "{value}"
            }}
        }}
    }}'''
    data = {'input_data': input_data}
    response = requests.put(url_update_udf.format(request_id=request_id), headers=headers, data=data, verify=False)
    if response.status_code == 200:
        print(f"Champ UDF mis à jour pour le ticket ID: {request_id} avec la valeur {value}.")
    else:
        print(f"Erreur lors de la mise à jour du champ UDF pour le ticket ID {request_id}: {response.status_code} - {response.text}")

# Fonction pour récupérer et traiter les demandes avec pagination
def check_requests():
    row_count = 100
    start_index = 1
    has_more_requests = True

    while has_more_requests:
        input_data = f'''{{
            "list_info": {{
                "row_count": {row_count},
                "start_index": {start_index}
            }}
        }}'''
        params = {'input_data': input_data}
        
        try:
            response = requests.get(url_requests, headers=headers, params=params, verify=False)
            print(f"Requête vers {url_requests} - Statut: {response.status_code} (Page: {start_index // row_count + 1})")
            
            if response.status_code == 200:
                data = response.json()
                requests_page = data.get('requests', [])
                if not requests_page:
                    has_more_requests = False
                    print("Aucune demande supplémentaire trouvée.")
                    break

                preventive_maintenance_requests = [req for req in requests_page if req['template']['name'] == "Maintenance Préventive"]

                for req in preventive_maintenance_requests:
                    ticket_id = req['id']
                    subject = req['subject']
                    attachment_response = requests.get(url_attachments.format(ticket_id=ticket_id), headers=headers, verify=False)
                    print(f"Requête pour les pièces jointes du ticket {ticket_id} - Statut: {attachment_response.status_code}")

                    if attachment_response.status_code == 200:
                        attachments_data = attachment_response.json()
                        attachments = attachments_data.get('attachments', [])
                        print(f"Pièces jointes trouvées pour le ticket {ticket_id}: {attachments}")

                        has_valid_attachment = any(attachment['name'].endswith(('.pdf', '.png', '.jpg','.jpeg')) for attachment in attachments)

                        if has_valid_attachment:
                            print(f"Présence de pièces jointes valides pour le ticket {ticket_id}: OUI")
                            update_udf(ticket_id, subject, "OUI")
                        else:
                            print(f"Présence de pièces jointes valides pour le ticket {ticket_id}: NON")
                            update_udf(ticket_id, subject, "NON")
                    else:
                        print(f"Erreur lors de la récupération des pièces jointes pour le ticket {ticket_id}: {attachment_response.status_code}")

                # Incrémenter l'index pour la page suivante
                start_index += row_count
            else:
                print(f"Erreur lors de la requête : {response.status_code} - {response.text}")
                has_more_requests = False
        except requests.RequestException as e:
            print(f"Erreur lors de la requête : {str(e)}")
            has_more_requests = False

# Exécution unique du script
check_requests()
print("Vérification terminée.")
