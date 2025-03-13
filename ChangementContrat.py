import requests
import json
import time
import os
from datetime import datetime

class ContractChangeMonitor:
    def __init__(self, auth_token, base_url, current_storage_path='current_contracts.json', previous_storage_path='previous_contracts.json'):
        self.auth_token = auth_token
        self.base_url = base_url
        self.current_storage_path = current_storage_path
        self.previous_storage_path = previous_storage_path
        self.current_contracts = self.load_contracts(self.current_storage_path)
        self.previous_contracts = self.load_contracts(self.previous_storage_path)

    def load_contracts(self, storage_path):
        """Load contracts from JSON file or create empty dict."""
        if os.path.exists(storage_path):
            try:
                with open(storage_path, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return {}
        return {}

    def save_contracts(self, contracts, storage_path):
        """Save contracts to JSON file."""
        with open(storage_path, 'w') as f:
            json.dump(contracts, f, indent=4)

    def get_all_contracts(self):
        """Fetch all contracts from the service desk API with pagination."""
        url = f"{self.base_url}/api/v3/contracts"
        headers = {"authtoken": self.auth_token}

        all_contracts = []
        start_index = 0
        row_count = 100

        while True:
            input_data = json.dumps({
                "list_info": {
                    "row_count": row_count,
                    "start_index": start_index
                }
            })
            params = {'input_data': input_data}

            try:
                response = requests.get(url, headers=headers, params=params, verify=False)
                response.raise_for_status()
                contracts_data = response.json()

                if not contracts_data.get('contracts'):
                    break

                all_contracts.extend(contracts_data['contracts'])

                if len(contracts_data['contracts']) < row_count:
                    break

                start_index += row_count

            except requests.exceptions.RequestException as e:
                print(f"Erreur de récupération des contrats: {e}")
                break

        return all_contracts

    def get_contract_details(self, contract_id):
        """Get details of a specific contract."""
        url = f"{self.base_url}/api/v3/contracts/{contract_id}"
        headers = {"authtoken": self.auth_token}

        try:
            response = requests.get(url, headers=headers, verify=False)
            response.raise_for_status()
            return response.json().get('contract', {})
        except requests.exceptions.RequestException as e:
            print(f"Erreur de récupération des détails du contrat {contract_id}: {e}")
            return None

    def compare_contracts(self, old_contract, new_contract):
        """Compare two contract details and identify changes."""
        changes = []

        def deep_compare(old_data, new_data, prefix=''):
            if isinstance(old_data, dict) and isinstance(new_data, dict):
                for key in set(list(old_data.keys()) + list(new_data.keys())):
                    full_key = f"{prefix}.{key}" if prefix else key
                    old_val = old_data.get(key)
                    new_val = new_data.get(key)

                    if old_val != new_val:
                        if isinstance(old_val, (dict, list)) and isinstance(new_val, type(old_val)):
                            deep_compare(old_val, new_val, full_key)
                        else:
                            changes.append({
                                'field': full_key,
                                'old_value': old_val,
                                'new_value': new_val,
                                'timestamp': datetime.now().isoformat()
                            })
            elif old_data != new_data:
                changes.append({
                    'field': prefix,
                    'old_value': old_data,
                    'new_value': new_data,
                    'timestamp': datetime.now().isoformat()
                })

        deep_compare(old_contract, new_contract)
        return changes

    def send_email_notification(self, contract_id, changes):
        """Send email notification for contract changes."""
        url = f"{self.base_url}/api/v3/requests/10972/notifications"
        headers = {"authtoken": self.auth_token}

        contract_details = self.get_contract_details(contract_id)

        contract_name = contract_details.get('name') or 'Contrat sans nom'
        contract_type = contract_details.get('type', {}).get('name') or 'Type non spécifié'
        contract_start_date = contract_details.get('from_date', {}).get('display_value') or 'Date de début non spécifiée'
        contract_end_date = contract_details.get('to_date', {}).get('display_value') or 'Date de fin non spécifiée'
        contract_assets = contract_details.get('assets', [])

        assets_description = "<br>".join([
            f"• {asset['name']}: {asset.get('product', {}).get('id')} - {asset.get('state', {}).get('id')}"
            for asset in contract_assets
        ]) if contract_assets else 'Aucun asset spécifié'

        change_description = "<br>".join([
            f"• {change['field']}: {change['old_value']} → {change['new_value']}"
            for change in changes
        ])

        input_data = json.dumps({
            "notification": {
                "subject": f"Changement de Contrat: {contract_name}",
                "description": f"""
                Bonjour,<br><br>
                Détails du Contrat:<br>
                • Nom: {contract_name}<br>
                • Type: {contract_type}<br>
                • Numéro de Contrat: {contract_id}<br>
                • Date de Début: {contract_start_date}<br>
                • Date de Fin: {contract_end_date}<br>
                • Assets:<br>
                {assets_description}<br><br>
                Changements Détectés:<br>
                {change_description}<br><br>
                Cordialement,<br>
                Système de Monitoring des Contrats
                """,
                "to": [{"email_id": ""}, ],
                "type": "reply"
            }
        })

        data = {'input_data': input_data}

        try:
            response = requests.post(url, headers=headers, data=data, verify=False)
            response.raise_for_status()
            print(f"Notification envoyée pour le contrat {contract_id}")
        except requests.exceptions.RequestException as e:
            print(f"Erreur lors de l'envoi de la notification: {e}")

    def monitor_contracts(self, check_interval=3600):
        """Continuously monitor contracts for changes."""
        # Check if the previous contracts file exists
        if not os.path.exists(self.previous_storage_path):
            # If not, create it with the current contracts data
            contracts = self.get_all_contracts()
            current_contracts = {}
            for contract in contracts:
                contract_id = str(contract.get('id'))
                if contract_id:
                    current_contract = self.get_contract_details(contract_id)
                    if current_contract:
                        current_contracts[contract_id] = current_contract
            self.save_contracts(current_contracts, self.previous_storage_path)
            print(f"Fichier {self.previous_storage_path} créé avec les données initiales des contrats.")

        while True:
            contracts = self.get_all_contracts()
            updated_contracts = {}

            for contract in contracts:
                contract_id = str(contract.get('id'))  # Convert to string for JSON compatibility

                if contract_id:
                    current_contract = self.get_contract_details(contract_id)

                    if current_contract:
                        # Check if contract exists in previous state
                        previous_contract = self.previous_contracts.get(contract_id, {})

                        # Compare contracts
                        changes = self.compare_contracts(previous_contract, current_contract)

                        if changes:
                            self.send_email_notification(contract_id, changes)

                        # Store updated contract
                        updated_contracts[contract_id] = current_contract

            # Update and save contracts
            self.previous_contracts = updated_contracts
            self.save_contracts(self.previous_contracts, self.previous_storage_path)
            self.save_contracts(updated_contracts, self.current_storage_path)

            # Wait before next check
            time.sleep(check_interval)

def main():
    BASE_URL = "https://xxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    AUTH_TOKEN = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

    monitor = ContractChangeMonitor(AUTH_TOKEN, BASE_URL)
    monitor.monitor_contracts()

if __name__ == "__main__":
    main()
