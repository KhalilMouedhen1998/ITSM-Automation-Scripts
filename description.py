import os
import requests
from bs4 import BeautifulSoup
import json
import google.generativeai as genai

# Configurer l'API de Google Generative AI
api_key = ""
os.environ["API_KEY"] = api_key
genai.configure(api_key=os.environ["API_KEY"])

# Fonction pour extraire les variables à l'aide du modèle
def extract_variables_with_genai(text):
    prompt = f"""
    Voici un texte contenant plusieurs informations techniques : 

    {text}

    Identifie et extrait les variables dans ce format : 
    - **Part number used (faulted PN)** : {{}} 
    - **FRU Description** : {{}} 
    - **Serial number used** : {{}} 
    - **Coût** : {{}}

    **Règles spécifiques** : 
    1. Le "Part number used" est toujours le premier numéro ou chaîne alphanumérique unique mentionné après la salutation. 
    2. La "FRU Description" est la ligne immédiatement après le "Part number used". 
    3. Le "Serial number used" est la variable immédiatement après la "FRU Description". Si aucun numéro de série n'est mentionné, indique "Non disponible". 
    4. Si plusieurs coûts sont mentionnés, sélectionne le coût minimum.
    """
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompt)
    extracted_text = response.text.strip()
    print(f"Variables extraites brutes :\n{extracted_text}")

    # Extraction des valeurs après les deux-points
    A = None  # Part number used
    B = None  # FRU Description
    C = "Non disponible"  # Serial number used
    D = "Non disponible"  # Cost

    # Extraire les valeurs après le signe ":"
    lines = extracted_text.split("\n")
    for line in lines:
        if "Part number used (faulted PN)" in line:
            A = line.split(":")[1].strip() if ":" in line else None
        elif "FRU Description" in line:
            B = line.split(":")[1].strip() if ":" in line else None
        elif "Serial number used" in line:
            C = line.split(":")[1].strip() if ":" in line else "Non disponible"
        elif "Coût" in line:
            D = line.split(":")[1].strip() if ":" in line else "Non disponible"

    return A, B, C, D

# Fonction pour vérifier si l'ID de demande a déjà été traité
def is_request_processed(request_id):
    with open("log.txt", "r") as log_file:
        processed_ids = log_file.readlines()
        return str(request_id) + "\n" in processed_ids

# Fonction pour ajouter un ID de demande au fichier de log
def log_processed_request(request_id):
    with open("log.txt", "a") as log_file:
        log_file.write(str(request_id) + "\n")

# Fonction principale pour traiter une description de tâche
def process_task_description(description):
    # Nettoyage du texte brut
    soup = BeautifulSoup(description, 'html.parser')
    cleaned_description = soup.get_text(separator="\n").strip()

    # Variables extraites par l'IA
    A, B, C, D = extract_variables_with_genai(cleaned_description)

    # Afficher les variables extraites
    print(f"Part number (A): {A}")
    print(f"FRU Description (B): {B}")
    print(f"Serial number (C): {C}")
    print(f"Coût (D): {D}")

    # Dictionnaire final avec les variables validées
    validated_variables = {
        "Part number used (faulted PN)": A,
        "FRU Description": B,
        "Serial number used": C,
        "Coût": D,
    }

    print(f"Variables validées : {validated_variables}")
    return validated_variables

# Fonction pour mettre à jour la demande via l'API
def update_request(api_url, headers, request_id, variables):
    update_url = f"{api_url}/requests/{request_id}"
    input_data = {
        "request": {
            "udf_fields": {
                "udf_sline_2494": variables.get("Serial number used", "Non disponible"),
                "udf_sline_2492": variables.get("Part number used (faulted PN)", ""),
                "udf_sline_2495": variables.get("Part number used (faulted PN)", ""),  # Répété
                "udf_sline_2484": variables.get("FRU Description", ""),
                "udf_sline_4801": variables.get("Coût", ""),
            }
        }
    }

    # Conversion en JSON
    json_input_data = {"input_data": json.dumps(input_data)}

    # Envoi de la requête PUT
    response = requests.put(update_url, headers=headers, data=json_input_data, verify=False)
    if response.status_code == 200:
        print(f"Demande ID {request_id} mise à jour avec succès.")
    else:
        print(f"Échec de la mise à jour pour la demande ID {request_id} : {response.status_code} - {response.text}")

# Script principal pour récupérer les demandes et les traiter
def main():
    requests_url = "/api/v3/requests"
    headers = {"authtoken": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"}
    input_data = '{"list_info": {"row_count": 100, "start_index": 1}}'
    params = {"input_data": input_data}

    # Récupération des demandes
    response = requests.get(requests_url, headers=headers, params=params, verify=False)

    if response.status_code == 200:
        requests_data = response.json()

        if "requests" in requests_data:
            for request in requests_data["requests"]:
                request_id = request["id"]
                print(f"Récupération des tâches pour la demande ID : {request_id}")

                # Vérification si la demande a déjà été traitée
                if is_request_processed(request_id):
                    print(f"Demande ID {request_id} déjà traitée. Passer au suivant.")
                    continue

                # URL de l'API pour récupérer les tâches pour cette demande
                tasks_url = f"/api/v3/requests/{request_id}/tasks"
                tasks_response = requests.get(tasks_url, headers=headers, verify=False)

                if tasks_response.status_code == 200:
                    tasks_data = tasks_response.json()
                    print(f"Tâches pour la demande ID {request_id}:")
                    if "tasks" in tasks_data:
                        for task in tasks_data["tasks"]:
                            if not task.get("template") or not task["template"].get("name"):
                                continue
                            if task["template"]["name"] == "Demande de BS":
                                task_id = task["id"]
                                print(f"Tâche trouvée : {task['template']['name']} (ID : {task_id})")

                                # URL pour récupérer les détails de cette tâche
                                task_details_url = f"/api/v3/requests/{request_id}/tasks/{task_id}"
                                task_details_response = requests.get(task_details_url, headers=headers, verify=False)

                                if task_details_response.status_code == 200:
                                    task_details = task_details_response.json()
                                    if "description" in task_details["task"]:
                                        html_description = task_details["task"]["description"]
                                        soup = BeautifulSoup(html_description, "html.parser")
                                        cleaned_description = soup.get_text(separator="\n").strip()
                                        print(f"Description de la tâche :\n{cleaned_description}")

                                        # Extraction des variables
                                        variables = process_task_description(cleaned_description)

                                        # Préparer et envoyer la mise à jour
                                        update_request("/api/v3", headers, request_id, variables)

                                        # Log de la demande traitée
                                        log_processed_request(request_id)
                                else:
                                    print(f"Erreur lors de la récupération des détails de la tâche : {task_details_response.text}")
                else:
                    print(f"Erreur lors de la récupération des tâches pour la demande : {tasks_response.text}")
        else:
            print("Aucune demande trouvée.")
    else:
        print(f"Erreur lors de la récupération des demandes : {response.text}")

if __name__ == "__main__":
    main()
