# Python version - 3.8
import requests
import json
from datetime import datetime

# Fonction pour récupérer les contrats
def get_contracts(headers):
    url = "https://service-desk.focus-corporation.com/api/v3/contracts"
    row_count = 10  # Nombre de contrats par requête
    start_index = 0
    contract_details = []

    while True:
        # Construire le JSON pour la pagination dans input_data
        input_data = {
            "list_info": {
                "row_count": row_count,
                "start_index": start_index
            }
        }
        params = {'input_data': json.dumps(input_data)}
        
        # Faire la requête GET
        response = requests.get(url, headers=headers, params=params, verify=False)
        
        # Vérifier si la requête a réussi
        if response.status_code != 200:
            print(f"Erreur lors de la requête : {response.status_code}")
            break

        # Charger la réponse en tant que JSON et accéder à la liste des contrats
        response_json = response.json()
        contracts = response_json.get('contracts', [])
        
        # Extraire et ajouter le nom, `to_date` et le statut pour chaque contrat
        for contract in contracts:
            name = contract.get('name', 'Nom non spécifié')
            to_date_str = contract.get('to_date', {}).get('display_value', 'Date de fin non spécifiée')
            
            # Vérifier si la date de fin est dépassée
            if to_date_str != 'Date de fin non spécifiée':
                to_date = datetime.strptime(to_date_str, "%d.%m.%Y")  # Convertir en objet datetime
                current_date = datetime.now()
                status = 'expiré' if to_date < current_date else 'actif'
            else:
                status = 'statut non spécifié'

            contract_details.append((name, status))
        
        # Condition de fin : arrêter si le nombre de contrats récupérés est inférieur à row_count
        if len(contracts) < row_count:
            break

        # Incrémenter start_index pour la page suivante
        start_index += row_count

    return contract_details

# Fonction principale pour récupérer les demandes
def get_requests(headers):
    url = "https://service-desk.focus-corporation.com/api/v3/requests"
    row_count = 100  # Nombre de demandes par requête
    max_pages = 5    # Nombre maximum de pages à récupérer
    all_requests = []

    # Récupérer jusqu'à max_pages de demandes
    for page in range(max_pages):
        start_index = page * row_count
        input_data = {
            "list_info": {
                "row_count": row_count,
                "start_index": start_index
            }
        }
        params = {'input_data': json.dumps(input_data)}

        # Faire la requête GET
        response = requests.get(url, headers=headers, params=params, verify=False)

        # Vérifier si la requête a réussi
        if response.status_code != 200:
            print(f"Erreur lors de la requête : {response.status_code}")
            break

        # Charger la réponse en tant que JSON et accéder à la liste des demandes
        response_json = response.json()
        requests_list = response_json.get('requests', [])
        all_requests.extend(requests_list)

        # Condition de fin : arrêter si nous avons récupéré suffisamment de demandes
        if len(requests_list) < row_count:
            break

    return all_requests

# Fonction pour mettre à jour le statut du contrat dans la demande
def update_request_status(request_id, statut, headers):
    url = f"https://service-desk.focus-corporation.com/api/v3/requests/{request_id}"
    input_data = json.dumps({
        "request": {
            "udf_fields": {
                "udf_sline_11401": statut
            }
        }
    })
    data = {'input_data': input_data}
    response = requests.put(url, headers=headers, data=data, verify=False)
    return response

# Main
if __name__ == "__main__":
    headers = {"authtoken": "906B26D6-70E5-4B71-BAF8-DCD21143B0EE"}

    # Récupérer les contrats
    contract_details = get_contracts(headers)

    # Récupérer les demandes
    all_requests = get_requests(headers)

    # Créer un dictionnaire pour les contrats avec leur statut
    contract_status_dict = {name: status for name, status in contract_details}

    # Traiter chaque demande pour obtenir les détails
    for request in all_requests:
        request_id = request.get('id')
        url_request_detail = f"https://service-desk.focus-corporation.com/api/v3/requests/{request_id}"
        
        response_detail = requests.get(url_request_detail, headers=headers, verify=False)
        
        if response_detail.status_code == 200:
            detail_json = response_detail.json()
            udf_fields = detail_json['request'].get('udf_fields', {})

            # Récupérer les champs souhaités
            udf_sline_11101 = udf_fields.get('udf_sline_11101', None)
            udf_pick_3910 = udf_fields.get('udf_pick_3910', None)

            # Déterminer le nom du contrat
            contrat = udf_sline_11101 if udf_sline_11101 else udf_pick_3910
            
            # Vérifier le statut du contrat
            statut = contract_status_dict.get(contrat, "Statut non spécifié")

            # Afficher les résultats
            print(f"Request ID: {request_id}, "
                  f"Contrat: {contrat}, "
                  f"Statut: {statut}")

            # Mettre à jour le statut dans la demande
            update_response = update_request_status(request_id, statut, headers)
            if update_response.status_code == 200:
                print(f"Statut mis à jour pour la demande ID {request_id}: {statut}")
            else:
                print(f"Erreur lors de la mise à jour du statut pour la demande ID {request_id}: {update_response.status_code}")
        else:
            print(f"Erreur lors de la requête pour le détail de la demande ID {request_id}: {response_detail.status_code}")
