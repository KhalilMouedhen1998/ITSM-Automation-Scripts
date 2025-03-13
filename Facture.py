import requests
import pandas as pd
import subprocess  # Import the subprocess module

# API URL and headers
base_url = "https://192.168.10.1/api/v3/contracts"
headers = {"authtoken": "906B26D6-70E5-4B71-BAF8-DCD21143B0EE"}

# Initial parameters to get all contracts
row_count = 100  # Adjust this value if API allows a higher limit
start_index = 0
all_contracts = []

# Step 1: Get all contracts
while True:
    input_data = f'''{{
        "list_info": {{
            "row_count": {row_count},
            "start_index": {start_index}
        }}
    }}'''
    
    params = {'input_data': input_data}
    response = requests.get(base_url, headers=headers, params=params, verify=False)

    if response.status_code == 200:
        data = response.json()
        contracts = data.get("contracts", [])
        
        if not contracts:
            break  # Exit loop if no more contracts are returned
        
        all_contracts.extend(contracts)
        start_index += row_count  # Move to the next page of results
    else:
        print(f"Error while fetching contracts: {response.status_code}")
        break

# Step 2: For each contract, get its assets and account name
contract_data_list = []  # List to hold contract data for DataFrame
for contract in all_contracts:
    contract_id = contract.get("id")
    contract_name = contract.get("name")
    account_info = contract.get("account", {})
    account_name = account_info.get("name", "Unknown Account")  # Default if account name not found

    # Make the API call for each contract to get its assets
    contract_url = f"{base_url}/{contract_id}"
    response = requests.get(contract_url, headers=headers, verify=False)

    if response.status_code == 200:
        contract_data = response.json().get("contract", {})
        assets = contract_data.get("assets", [])

        # Add contract data to the list
        if assets:
            for asset in assets:
                asset_name = asset.get("name")
                contract_data_list.append({
                    "Contract Name": contract_name,
                    "Account Name": account_name,
                    "Asset Name": asset_name
                })
        else:
            contract_data_list.append({
                "Contract Name": contract_name,
                "Account Name": account_name,
                "Asset Name": "No assets found"
            })
    else:
        print(f"Error fetching contract {contract_id}: {response.status_code}")

# Step 3: Create a DataFrame and save it to Excel
df = pd.DataFrame(contract_data_list)
output_file = "contracts_info.xlsx"
df.to_excel(output_file, index=False)

print(f"Data has been written to {output_file}")

# Step 4: Execute detailRequest.py
subprocess.run(["python", "détailRequest.py"], check=True)  # Adjust the command if necessary
