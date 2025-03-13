import requests
from datetime import datetime, time
import subprocess
import re

def get_astreinte_tech(ticket_creation_date):
    """Appelle le script astreinte.py et récupère le technicien d'astreinte pour la date de création du ticket"""
    process = subprocess.Popen(['python', 'astreinte.py'], 
                             stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE,
                             text=True)
    
    output, _ = process.communicate(input=f"{ticket_creation_date}\n")
    
    match = re.search(r"Astreinte Niveau 2: (.+)$", output, re.MULTILINE)
    if match:
        return match.group(1).strip()
    return None

def get_current_tickets():
    """Appelle le script NIV2-INFRA.py et récupère les informations des tickets"""
    result = subprocess.run(['python', 'NIV2-INFRA.py'], capture_output=True, text=True)
    output = result.stdout
    
    tickets = []
    current_ticket = {}
    
    for line in output.split('\n'):
        if 'Ticket ID:' in line:
            if current_ticket:
                tickets.append(current_ticket.copy())
            current_ticket = {}
            current_ticket['id'] = line.split(':')[1].strip()
        elif 'Date de création:' in line:
            date_str = line.split(':', 1)[1].strip()  # Utiliser split avec maxsplit=1
            try:
                # Essayer d'abord le format avec PM/AM
                current_ticket['creation_date'] = datetime.strptime(date_str, '%d/%m/%Y %I:%M %p')
            except ValueError:
                try:
                    # Essayer ensuite le format 24h
                    current_ticket['creation_date'] = datetime.strptime(date_str, '%d/%m/%Y %H:%M')
                except ValueError:
                    print(f"Erreur: Impossible de parser la date: {date_str}")
                    current_ticket['creation_date'] = datetime.now()  # Utiliser la date actuelle par défaut
        elif 'Technicien recommandé:' in line:
            current_ticket['technician'] = line.split(':')[1].strip()
    
    if current_ticket:
        tickets.append(current_ticket)
        
    return tickets

def is_holiday_2025(date):
    """Vérifie si la date est un jour férié en 2025"""
    holidays_2025 = {
        "2025-03-20",  # Independence Day
        "2025-03-30",  # Eid al-Fitr
        "2025-03-31",  # Eid al-Fitr Holiday
        "2025-05-01",  # Labour Day
        "2025-06-06",  # Eid al-Adha
        "2025-06-07",  # Eid al-Adha Holiday
        "2025-06-26",  # Muharram
        "2025-07-25",  # Republic Day
        "2025-09-04",  # Prophet's Birthday
        "2025-12-17",  # Revolution and Youth Day
    }
    return date.strftime('%Y-%m-%d') in holidays_2025

def is_astreinte_hours(dt):
    """Vérifie si l'heure est en période d'astreinte"""
    time_of_day = dt.time()
    return time_of_day >= time(17, 30) or time_of_day < time(8, 29)

def is_weekend(dt):
    """Vérifie si c'est un weekend"""
    return dt.weekday() >= 5

def assign_ticket(ticket_id, technician):
    """Assigne le ticket au technicien via l'API"""
    url = f"https://10.10.30.75/api/v3/requests/{ticket_id}/assign"
    headers = {"authtoken": "0C865686-02A7-45EE-B13A-8C22A1066429"}
    
    input_data = f'''{{
        "request": {{
            "group": {{
                "name": "Professional Services"
            }},
            "technician": {{
                "name": "{technician}"
            }}
        }}
    }}'''
    
    data = {'input_data': input_data}
    
    try:
        response = requests.put(
            url,
            headers=headers,
            data=data,
            verify=False
        )
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Erreur lors de l'assignation du ticket {ticket_id}: {str(e)}")
        return None
        
def is_ticket_assigned(ticket_id):
    """Vérifie si l'ID du ticket est déjà dans le fichier des tickets assignés"""
    try:
        with open('assigned_tickets.txt', 'r') as file:
            assigned_tickets = file.readlines()
        assigned_tickets = [ticket.strip() for ticket in assigned_tickets]
        return ticket_id in assigned_tickets
    except FileNotFoundError:
        return False

def mark_ticket_as_assigned(ticket_id):
    """Ajoute l'ID du ticket au fichier des tickets assignés"""
    with open('assigned_tickets.txt', 'a') as file:
        file.write(f"{ticket_id}\n")

def main():
    print("Chargement des tickets en cours...")
    
    # Récupérer tous les tickets actuels
    tickets = get_current_tickets()
    
    print("\nTraitement des tickets en cours...\n")
    
    for ticket in tickets:
        creation_date = ticket['creation_date']
        
        # Vérifier si le ticket a déjà été assigné
        if is_ticket_assigned(ticket['id']):
            print(f"Ticket {ticket['id']} déjà assigné. Ignoré.")
            continue
        
        # Récupérer le technicien d'astreinte pour la date de création du ticket
        astreinte_tech = get_astreinte_tech(creation_date.strftime('%d/%m/%Y'))
        
        print(f"\nTechnicien d'astreinte pour le ticket {ticket['id']} (créé le {creation_date.strftime('%d/%m/%Y')}): {astreinte_tech}")
        
        # Vérifier si c'est une période d'astreinte
        is_astreinte = (
            is_astreinte_hours(creation_date) or
            is_weekend(creation_date) or
            is_holiday_2025(creation_date)
        )
        
        # Déterminer le technicien à assigner
        if is_astreinte:
            tech_to_assign = astreinte_tech
            status = "ASTREINTE"
        else:
            tech_to_assign = ticket['technician']
            status = "NORMAL"
            
        # Assigner le ticket
        result = assign_ticket(ticket['id'], tech_to_assign)
        
        if result:
            mark_ticket_as_assigned(ticket['id'])
            print(f"Ticket {ticket['id']}:")
            print(f"  Date de création: {creation_date.strftime('%d/%m/%Y %H:%M')}") 
            print(f"  Status: {status}")
            print(f"  Assigné à: {tech_to_assign}")
            print("  ✓ Assignation réussie")
        else:
            print(f"Ticket {ticket['id']} non assigné.")
        
        print("-" * 50)

if __name__ == "__main__":
    main()
