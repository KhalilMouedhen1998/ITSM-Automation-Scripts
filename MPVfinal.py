import requests
import json
import time
import os
from datetime import datetime, timedelta

# Configuration API
url_get = "https://service-desk.focus-corporation.com/api/v3/requests"
url_edit = "https://service-desk.focus-corporation.com/api/v3/requests/{request_id}"
headers = {"authtoken": "906B26D6-70E5-4B71-BAF8-DCD21143B0EE"}
verify_ssl = False

# Fichier de suivi des tickets traités
processed_file = "processed_requests.json"
log_file = "update_logs.txt"

# Conversion du temps en millisecondes
MILLISECONDS_IN_A_DAY = 86400000

# Fonction pour enregistrer les logs
def log_message(message):
    with open(log_file, 'a') as log:
        log.write(f"{datetime.now()}: {message}\n")

# Fonction pour remplacer "Date fixe ()" par la date limite
def replace_date_fixe_with_due_date(title, due_date):
    if "Date fixe ()" in title:
        due_date_str = due_date.strftime("%d/%m/%Y")
        new_title = title.replace("Date fixe ()", f"Date fixe ({due_date_str})")
        return new_title
    return title

# Fonction pour calculer la date de fin en millisecondes
def calculate_end_date_in_ms(created_date, months_to_add):
    end_date = created_date + timedelta(days=months_to_add * 30)
    end_date_ms = int(end_date.timestamp() * 1000)  # Convertir en millisecondes
    return end_date_ms

# Fonction pour mettre à jour le ticket via l'API
def update_request(request_id, new_title):
    url = url_edit.format(request_id=request_id)
    input_data = {
        "request": {
            "subject": new_title,
        }
    }

    data = {'input_data': json.dumps(input_data)}
    log_message(f"Sending update for request {request_id} with title: '{new_title}'")
    response = requests.put(url, headers=headers, data=data, verify=verify_ssl)

    if response.status_code == 200:
        log_message(f"Request {request_id} successfully updated with title '{new_title}'")
        return True
    else:
        log_message(f"Error updating request {request_id}: {response.status_code} - {response.text}")
        return False

# Fonction pour mettre à jour les UDF du ticket
def update_udf(request_id, end_date_ms, due_date_ms):
    url = url_edit.format(request_id=request_id)
    input_data = {
        "request": {
            "udf_fields": {
                "udf_date_10801": {  # Remplacez par le champ correct pour DF
                    "value": str(end_date_ms)
                },
                "udf_date_4227": {  # Remplacez par le champ correct pour la date limite
                    "value": str(due_date_ms)
                }
            }
        }
    }

    data = {'input_data': json.dumps(input_data)}
    log_message(f"Updating UDF for request {request_id} with end date: {end_date_ms} and due date: {due_date_ms}")
    response = requests.put(url, headers=headers, data=data, verify=verify_ssl)

    if response.status_code == 200:
        log_message(f"UDF for request {request_id} successfully updated.")
    else:
        log_message(f"Error updating UDF for request {request_id}: {response.status_code} - {response.text}")

# Récupérer un seul ticket
def get_single_request():
    input_data = '''{
        "list_info": {
            "row_count": 1
        }
    }'''
    params = {'input_data': input_data}
    response = requests.get(url_get, headers=headers, params=params, verify=verify_ssl)

    if response.status_code == 200:
        requests_list = response.json().get("requests", [])
        return requests_list[0] if requests_list else None
    else:
        log_message(f"Error fetching requests: {response.status_code} - {response.text}")
        return None

# Lire les IDs des tickets traités depuis le fichier
def read_processed_ids():
    if os.path.exists(processed_file):
        with open(processed_file, 'r') as file:
            return json.load(file)  # Charger le dictionnaire JSON
    else:
        log_message(f"File {processed_file} does not exist. Creating a new one.")
        with open(processed_file, 'w') as file:
            json.dump({}, file)  # Créer le fichier
        return {}

# Écrire les IDs des tickets traités dans le fichier
def write_processed_id(processed_ids, request_id, update_count):
    processed_ids[request_id] = update_count
    with open(processed_file, 'w') as file:
        json.dump(processed_ids, file)  # Sauvegarder le dictionnaire JSON

# Convertir la date string en objet datetime
def parse_created_date(date_data):
    if isinstance(date_data, dict):
        date_str = date_data.get('display_value')
        if date_str:
            try:
                return datetime.strptime(date_str, "%d/%m/%Y %I:%M %p")
            except ValueError:
                log_message(f"Erreur lors de la conversion de la date: {date_str}")
                return None
    else:
        log_message(f"Date format non supporté: {date_data}")
        return None

# Fonction pour mettre à jour le cycle
# Fonction pour mettre à jour le cycle
def update_cycle(title, created_date, request_id):
    current_month = created_date.month
    current_year = created_date.year
    period = None
    semester = None
    months_to_add = 0

    # Détermination de la période et du mois à ajouter
    if 1 <= current_month <= 3:
        period = "Trimestre (1)"
        months_to_add = 3
        semester = "Semestre (1)"
    elif 4 <= current_month <= 6:
        period = "Trimestre (2)"
        months_to_add = 3
        semester = "Semestre (1)"
    elif 7 <= current_month <= 9: 
        period = "Trimestre (3)"
        months_to_add = 3
        semester = "Semestre (2)"
    elif 10 <= current_month <= 12:
        period = "Trimestre (4)"
        months_to_add = 3
        semester = "Semestre (2)"

    # Vérifier si le sujet contient "Semestre" et définir months_to_add
    if "Semestre" in title:
        months_to_add = 6  # Pour les semestres, ajoutez 6 mois

    new_title = title
    if "Trimestre" in title and period not in title:
        new_title = title.replace("Trimestre (1)", period).replace("Trimestre (2)", period).replace("Trimestre (3)", period).replace("Trimestre (4)", period)

    if "Semestre" in title and semester not in title:
        new_title = title.replace("Semestre (1)", semester).replace("Semestre (2)", semester)

    # Calcul de la date limite
    due_date = created_date
    if "Trimestre" in title:
        due_date += timedelta(days=20)  # Ajoute 20 jours pour le trimestre
    elif "Semestre" in title:
        due_date += timedelta(days=61)  # Ajoute 60 jours pour le semestre

    # Remplacer "Date fixe ()" par la date limite, si applicable
    new_title = replace_date_fixe_with_due_date(new_title, due_date)



    return new_title, period, semester, months_to_add

# Fonction pour mettre à jour la date limite
def update_due_date(request_id, created_date, subject):
    due_date = created_date
    if "Trimestre" in subject:
        due_date += timedelta(days=20)  # Ajoute 20 jours pour le trimestre
    elif "Semestre" in subject:
        due_date += timedelta(days=61)  # Ajoute 60 jours pour le semestre

    due_date_ms = int(due_date.timestamp() * 1000)  # Convertir en millisecondes

    return due_date_ms

# Main
# Main
def main():
    processed_ids = read_processed_ids()

    ticket = get_single_request()
    if not ticket:
        log_message("No tickets found to process.")
        return

    request_id = ticket['id']
    subject = ticket['subject']
    created_date = parse_created_date(ticket.get('created_time'))
    if not created_date:
        log_message("Skipping ticket due to missing created date.")
        return

    # Si le ticket a déjà été traité deux fois, ignorer
    if request_id in processed_ids and processed_ids[request_id] >= 2:
        log_message(f"Request {request_id} already processed twice. Skipping.")
        return

    # Mise à jour du cycle et obtention des nouvelles dates
    new_title, period, semester, months_to_add = update_cycle(subject, created_date, request_id)

    if new_title != subject:
        if update_request(request_id, new_title):
            write_processed_id(processed_ids, request_id, processed_ids.get(request_id, 0) + 1)

    end_date_ms = calculate_end_date_in_ms(created_date, months_to_add)
    due_date_ms = update_due_date(request_id, created_date, subject)

    update_udf(request_id, end_date_ms, due_date_ms)

if __name__ == "__main__":
    main()
