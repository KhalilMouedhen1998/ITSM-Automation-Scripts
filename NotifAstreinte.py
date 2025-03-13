import requests
from datetime import datetime

# Dictionnaire des adresses email des ingénieurs
EMAILS = {
    # Équipe 1
    "Khalil Nakhli": "medkhalil.nakhli@focus-corporation.com",
    "Thamer Litimi": "thamer.litimi@focus-corporation.com",
    "Ramzi Gharbi": "ramzi.gharbi@focus-corporation.comm",
    "Moughith Salhi": "moughith.salhi@focus-corporation.com",
    
    # Équipe 2
    "Hamdi Merriah": "hamdi.meriah@focus-corporation.comm",
    "Mahmoud Hermi": "mahmoud.hermi@focus-corporation.com",
    "Oussama Guizani": "oussema.guizani@focus-corporation.com",
    "AlaaEddine Majdoub": "alaaeddine.majdoub@focus-corporation.com",
    "Oussama Rouiss": "oussama.rouis@focus-corporation.com",
    "Ridha Kaaniche": "medridha.kaaniche@focus-corporation.com",
    
    # Équipe Cloud
    "Med Said Ben Guirat": "medsaid.benguirat@focus-corporation.com",
    "Nader Gharsalli": "nader.gharsalli@focus-corporation.comm",
    "Hamza Balti": "hamza.balti@focus-corporation.com",
    "Skander Lazgheb": "skander.lazghab@focus-corporation.com",
    "Houssem Ghazouani": "houssem.ghazouani@focus-corporation.com",
    
    # Équipe Network/Security et SOC
    "Amine Ben Messaoud": "amine.benmessaoud@focus-corporation.comm",
    "Ahmed Kalai": "Ahmed.kalai@focus-corporation.com",
    "Islem CHERIF": "islem.cherif@focus-corporation.comm",
    "Med Aziz Mettichi": "medaziz.mettichi@focus-corporation.com"
}

def parse_astreinte_output(output_text):
    """Parse le texte de sortie du script d'astreinte"""
    engineers = {}
    lines = output_text.split('\n')
    for line in lines:
        if ':' in line and ('Niveau' in line or 'Cloud' in line or 'Network' in line or 'SOC' in line):
            role, name = line.split(': ')
            engineers[role.strip()] = name.strip()
    return engineers

def send_notification(engineer_name, role, week_number):
    """Envoie une notification à l'ingénieur d'astreinte"""
    if engineer_name not in EMAILS:
        print(f"Erreur: Adresse email non trouvée pour {engineer_name}")
        return False
    
    url = "https://service-desk.focus-corporation.com/api/v3/requests/10972/notifications"
    headers = {"authtoken": "906B26D6-70E5-4B71-BAF8-DCD21143B0EE"}
    
    notification_data = {
        "notification": {
            "subject": f"Rappel: Astreinte semaine {week_number}",
            "description": f"""
                Bonjour {engineer_name},<br><br>Ce message est pour vous rappeler que vous êtes d'astreinte cette semaine (semaine {week_number}) <br> <br>Merci de rester joignable pendant votre période d'astreinte.<br><br>Cordialement,<br>Support FOCUS
            """,
            "to": [{"email_id": EMAILS[engineer_name]}, {"email_id": "khalil.mouadhen@focus-corporation.com"}],
            "type": "reply"
        }
    }
    
    data = {'input_data': str(notification_data)}
    try:
        response = requests.post(url, headers=headers, data=data, verify=False)
        if response.status_code == 200:
            print(f"✓ Email envoyé avec succès à {engineer_name} ({EMAILS[engineer_name]})")
            return True
        else:
            print(f"✗ Échec de l'envoi à {engineer_name}: Status code {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Erreur lors de l'envoi à {engineer_name}: {str(e)}")
        return False

def main():
    # Exemple de sortie du script d'astreinte
    astreinte_output = """Semaine actuelle : 7
    Techniciens d'astreinte pour aujourd'hui:
    Niveau 1: Ramzi Gharbi
    Niveau 2: Hamdi Merriah
    Cloud: Nader Gharsalli
    Network/Security: Amine Ben Messaoud
    SOC: Islem CHERIF"""
    
    # Récupérer le numéro de la semaine
    week_number = datetime.now().isocalendar()[1]
    
    # Parser la sortie
    engineers = parse_astreinte_output(astreinte_output)
    
    # Envoyer les notifications
    success_count = 0
    total_count = len(engineers)
    
    for role, engineer in engineers.items():
        if send_notification(engineer, role, week_number):
            success_count += 1
    
    print(f"\nRésumé: {success_count}/{total_count} notifications envoyées avec succès")

if __name__ == "__main__":
    main()