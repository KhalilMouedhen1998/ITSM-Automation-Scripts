import requests
import json
from datetime import datetime, timedelta

# Configuration de l'API pour récupérer les contrats
url_contracts = "https://service-desk.focus-corporation.com/api/v3/contracts"
headers = {"authtoken": "906B26D6-70E5-4B71-BAF8-DCD21143B0EE"}

row_count = 10  # Nombre de contrats par requête
start_index = 0
contract_ids = []

# Récupération des IDs de contrats avec pagination
while True:
    input_data = {
        "list_info": {
            "row_count": row_count,
            "start_index": start_index
        }
    }
    params = {'input_data': json.dumps(input_data)}

    try:
        response = requests.get(url_contracts, headers=headers, params=params, verify=False)
        response.raise_for_status()  # Vérifie si la requête a échoué

        response_json = response.json()
        contracts = response_json.get('contracts', [])

        # Affiche le nombre de contrats récupérés dans cette requête
        print(f"Contrats récupérés : {len(contracts)}")

        for contract in contracts:
            contract_id = contract.get('id')
            contract_name = contract.get('name', 'Nom non spécifié')  # Récupère le nom
            contract_status = contract.get('status', {}).get('status', 'Statut non spécifié')  # Récupère le statut

            # Vérifie si le contrat est actif
            if contract_status == "Active":
                print(f"ID: {contract_id}, Nom: {contract_name}, Statut: {contract_status}")  # Affiche ID, nom et statut

                if contract_id is not None:
                    contract_ids.append(contract_id)

        # Si le nombre de contrats récupérés est inférieur à row_count, on suppose qu'on a atteint la fin
        if len(contracts) < row_count:
            break

        start_index += row_count

    except requests.exceptions.HTTPError as err:
        print(f"Erreur lors de la requête : {err}")
        break
    except json.JSONDecodeError:
        print("Erreur de décodage JSON dans la réponse.")
        break
    except Exception as e:
        print(f"Une erreur est survenue : {e}")
        break

# Récupération des détails de chaque contrat actif à partir de leurs IDs
active_contract_details = []
for contract_id in contract_ids:
    url_detail = f"https://service-desk.focus-corporation.com/api/v3/contracts/{contract_id}"
    
    try:
        response = requests.get(url_detail, headers=headers, verify=False)
        response.raise_for_status()  # Vérifie si la requête a échoué

        details = response.json().get("contract", {})  # Chargement de la réponse en JSON et accès à la clé "contract"

        # Vérifier si le statut du contrat est "Active"
        if details.get("status", {}).get("status") == "Active":
            # Récupération des champs personnalisés
            udf_fields = details.get("udf_fields", {})
            udf_date_9936 = udf_fields.get("udf_date_9936", {}).get("display_value", "Date non spécifiée")
            udf_date_9935 = udf_fields.get("udf_date_9935", {}).get("display_value", "Date non spécifiée")
            
            # Stocker la date originale dans une variable
            date_reception_definitive = udf_date_9936
            
            # Supprime l'heure et AM/PM de la date définitive
            if udf_date_9936:
                udf_date_9936 = date_reception_definitive.split()[0]  # On prend seulement la date (avant l'espace)
                
            # Supprime l'heure et AM/PM de la date provisoire
            if udf_date_9935:
                udf_date_9935 = udf_date_9935.split()[0]  # On prend seulement la date (avant l'espace)

            # Convertir la date de réception définitive en format datetime
            try:
                date_reception_datetime = datetime.strptime(udf_date_9936, "%d/%m/%Y")
                
                # Calculer la date d'aujourd'hui + 2 semaines
                deux_semaines_plus_tard = (datetime.now() + timedelta(days=14)).replace(hour=0, minute=0, second=0, microsecond=0)
                print(deux_semaines_plus_tard);
                print(date_reception_datetime);
                print(datetime.now());
                
                # Vérification pour Verif
                verif = "oui" if (date_reception_datetime >= datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)  and date_reception_datetime == deux_semaines_plus_tard) else "non"
                
            except ValueError:
                verif = "Date invalide"

            # Ajout des détails dans la liste
            active_contract_details.append({
                "id": contract_id,
                "name": details.get('name', 'Nom non spécifié'),
                "status": details.get('status', {}).get('status', 'Statut non spécifié'),
                "udf_date_9936": udf_date_9936,
                "date_reception_definitive": date_reception_definitive,  # Conserver la date originale
                "udf_date_9935": udf_date_9935,  # Date de réception provisoire sans heure
                "verif": verif  # Ajout de la vérification
            })

            # Envoi de l'email si verif == "oui"
            if verif == "oui":
                contract_name = details.get('name', 'Nom non spécifié')
                print(contract_name,"piw");
                url = f"https://service-desk.focus-corporation.com/api/v3/requests/10972/notifications"
                input_data = {
                    "notification": {
                        "subject": "Rappel – Date de Réception Définitive",
                        "description": f"Bonjour,<br><br>Nous vous informons que la signature du procès-verbal de réception provisoire a eu lieu le {udf_date_9935} et que la date de réception définitive pour le contrat {contract_name} est prévue à la date du {udf_date_9936}.<br><br> Nous vous remercions de bien vouloir signer le procès verbal de réception définitive dans les délais souhaités et faire parvenir une copie au service logistique et l'équipe support.<br><br>Cordialement,<br>Support FOCUS",
                        "to": [
                            {"email_id": "karim.khalfaoui@focus-corporation.com"},
                            {"email_id": "mourad.belkhodja@focus-corporation.com"},
                            {"email_id": "mourad.ben-nasr@focus-corporation.com"},
                            {"email_id": "medhoussein.sayah@focus-corporation.com"}
                        ],
                        "cc": [
                            {"email_id": "khalil.mouadhen@focus-corporation.com"},
                            
                        ],
                        "type": "reply"
                    }
                }
                data = {'input_data': json.dumps(input_data)}
                response = requests.post(url, headers=headers, data=data, verify=False)
                
                # Vérification de la réponse et affichage du message approprié
                if response.status_code == 200:
                    print(f"Mail envoyé avec succès pour le contrat ID: {contract_id}.")
                else:
                    print(f"Erreur lors de l'envoi de l'email pour le contrat ID {contract_id}: {response.text}")

    except requests.exceptions.HTTPError as err:
        print(f"Erreur lors de la récupération des détails pour le contrat ID {contract_id}: {err}")
    except json.JSONDecodeError:
        print(f"Erreur de décodage JSON pour le contrat ID {contract_id}.")
    except Exception as e:
        print(f"Une erreur est survenue lors de la récupération des détails pour le contrat ID {contract_id}: {e}")

# Affiche les détails des contrats actifs récupérés
if active_contract_details:
    print("Contrats actifs récupérés :")
    for detail in active_contract_details:
        # Afficher l'ID, le nom, le statut, udf_date_9936, date de réception définitive et verif
        if detail["verif"] == "oui":
            print(f"Mail envoyé avec succès pour le contrat ID: {detail['id']}, Nom: {detail['name']}, Statut: {detail['status']}, Date de réception définitive: {detail['date_reception_definitive']}, Verif: {detail['verif']}")
        else:
            print(f"ID: {detail['id']}, Nom: {detail['name']}, Statut: {detail['status']}, Date de réception définitive: {detail['date_reception_definitive']}, Verif: {detail['verif']}")
else:
    print("Aucun contrat actif trouvé.")
