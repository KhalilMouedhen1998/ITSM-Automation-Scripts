import requests
import chardet
from collections import defaultdict

# Désactiver les avertissements pour les requêtes HTTPS non vérifiées
requests.packages.urllib3.disable_warnings()

def detect_encoding(filename):
    """Détecte l'encodage du fichier pour éviter les erreurs de lecture"""
    with open(filename, 'rb') as file:
        raw_data = file.read()
    result = chardet.detect(raw_data)
    return result['encoding']

def convert_to_utf8(filename, detected_encoding):
    """Convertit le fichier en UTF-8 si l'encodage est différent"""
    if detected_encoding.lower() != 'utf-8':
        utf8_filename = filename.replace(".txt", "_utf8.txt")
        with open(filename, 'r', encoding=detected_encoding, errors='replace') as f:
            content = f.read()
        with open(utf8_filename, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Fichier converti en UTF-8 : {utf8_filename}")
        return utf8_filename
    return filename

def read_and_process_file(filename):
    """Lit le fichier et calcule le total des heures journalières (HJ) par contrat"""
    contract_totals = defaultdict(float)
    contract_tickets = defaultdict(list)

    encoding_detected = detect_encoding(filename)
    filename = convert_to_utf8(filename, encoding_detected)

    with open(filename, 'r', encoding='utf-8', errors='replace') as file:
        for line in file:
            columns = line.strip().split('|')
            if len(columns) >= 5:
                ticket_id = columns[0]
                contract_name = columns[2]
                try:
                    hj_consumed = float(columns[4])  # Prend la colonne 5 (index 4)
                    contract_totals[contract_name] += hj_consumed
                    contract_tickets[contract_name].append(ticket_id)
                except ValueError as e:
                    print(f"Erreur de conversion pour le ticket {ticket_id}: {str(e)}")

    return contract_totals, contract_tickets

def update_ticket(ticket_id, total_hj):
    """Envoie une requête PUT à l'API pour mettre à jour le ticket"""
    url = f"https://192.168.10.1/api/v3/requests/{ticket_id}"
    headers = {
        "authtoken": "906B26D6-70E5-4B71-BAF8-DCD21143B0EE"
    }

    # Format JSON correct
    input_data = '''{
    "request": {
        "udf_fields": {
            "udf_decimal_4229": "%s"
        }
    }
}''' % str(total_hj)

    data = {'input_data': input_data}

    try:
        response = requests.put(url, headers=headers, data=data, verify=False)
        print(f"Status code: {response.status_code}")
        print(f"Response content: {response.text}")

        if response.status_code != 200:
            print(f"Détails de la requête échouée:")
            print(f"URL: {url}")
            print(f"Headers: {headers}")
            print(f"Data: {data}")

        return response.status_code == 200
    except Exception as e:
        print(f"Exception complète pour le ticket {ticket_id}:")
        print(f"Type d'erreur: {type(e).__name__}")
        print(f"Message d'erreur: {str(e)}")
        return False

def main():
    """Exécute le programme principal"""
    try:
        filename = 'processed_requests.txt'
        contract_totals, contract_tickets = read_and_process_file(filename)

        print("\nTotaux calculés par contrat:")
        for contract, total in contract_totals.items():
            print(f"{contract}: {total} HJ")

        print("\nDébut des mises à jour:")
        for contract, total in contract_totals.items():
            print(f"\nContrat: {contract}")
            print(f"Total HJ: {total}")

            for ticket_id in contract_tickets[contract]:
                print(f"\nTraitement du ticket {ticket_id}...")
                success = update_ticket(ticket_id, total)
                status = "réussi" if success else "échoué"
                print(f"Statut de la mise à jour: {status}")

    except Exception as e:
        print(f"Erreur générale: {str(e)}")

if __name__ == "__main__":
    main()
