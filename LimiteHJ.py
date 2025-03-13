import pandas as pd
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def check_assistance_limits(file_path, sheet_name):
    try:
        df = pd.read_excel(file_path, sheet_name=sheet_name, header=None)
        df.columns = ['Nom du contrat', 'Nombre de jours', 'Consommé', 'Limite']
    except Exception as e:
        print(f"Erreur lecture fichier Excel : {e}")
        return []

    url = "https://service-desk.focus-corporation.com/api/v3/requests/10972/notifications"
    headers = {"authtoken":"906B26D6-70E5-4B71-BAF8-DCD21143B0EE"}

    contrats_limite = []

    for index, row in df.iterrows():
        if pd.isna(row['Nombre de jours']) or pd.isna(row['Limite']):
            continue

        if row['Nombre de jours'] == row['Limite']:
            contrat = row['Nom du contrat']
            contrats_limite.append(contrat)

            input_data = '''{
    "notification": {
        "subject": "Assistance Technique - Limite HJ - Contrat %s",
        "description": "Les Hommes/Jours du contrat %s ont atteint leur limite.",
        "to": [
            {
                "email_id": "khalil.mouadhen@focus-corporation.com"
            },
            {
                "email_id": "medhoussein.sayah@focus-corporation.com"
            }

        ],
        "type": "reply"
    }
}''' % (contrat, contrat)

            data = {'input_data': input_data}

            try:
                response = requests.post(url, headers=headers, data=data, verify=False)
                
                print(f"Réponse pour {contrat} : {response.text}")
                
                if response.status_code == 200:
                    print(f"Notification envoyée pour le contrat : {contrat}")
                else:
                    print(f"Échec notification pour {contrat}. Statut : {response.status_code}")
            
            except requests.exceptions.RequestException as e:
                print(f"Erreur notification : {e}")

    return contrats_limite

def main():
    file_path = r"\\shares\FTS_Helpdesk\Etat assistances Hommes Jours Clients 2025.xlsx"
    sheet_name = "HJ"

    contrats_a_limite = check_assistance_limits(file_path, sheet_name)
    
    if contrats_a_limite:
        print("Contrats ayant atteint leur limite :")
        for contrat in contrats_a_limite:
            print(f"- {contrat}")
    else:
        print("Aucun contrat n'a atteint sa limite d'assistance.")

if __name__ == "__main__":
    main()