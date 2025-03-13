import requests
import pandas as pd

# Function to get all requests and their details with pagination
def fetch_requests():
    url = "/api/v3/requests"
    headers = {"authtoken": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"}

    all_requests = []
    page = 1
    while True:
        input_data = f'''{{
            "list_info": {{
                "row_count": 100,
                "page": {page}
            }}
        }}'''

        params = {'input_data': input_data}
        response = requests.get(url, headers=headers, params=params, verify=False)

        if response.status_code == 200:
            requests_data = response.json().get("requests", [])
            all_requests.extend(requests_data)
            if len(requests_data) < 100:  # Assuming 100 is the max per page
                break  # No more pages to fetch
            page += 1  # Go to the next page
        else:
            print(f"Error fetching requests: {response.status_code} - {response.text}")
            break

    return all_requests

# Function to get details of a specific request
def fetch_request_details(request_id):
    url = f"/api/v3/requests/{request_id}"
    headers = {"authtoken": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"}
    response = requests.get(url, headers=headers, verify=False)

    if response.status_code == 200:
        return response.json().get("request", {})
    else:
        print(f"Error fetching request {request_id}: {response.status_code} - {response.text}")
        return {}

# Function to load account names and asset names from Excel
def load_contracts_info(file_path):
    df = pd.read_excel(file_path)
    print("Columns in Excel:", df.columns.tolist())  # Print columns for debugging
    # Clean column names and trim whitespace
    df.columns = df.columns.str.strip()
    for col in df.columns:
        df[col] = df[col].str.strip()  # Trim whitespace from all string entries
    return df

# Function to update request with the contract name
def update_request(request_id, contract_name):
    url = f"/api/v3/requests/{request_id}"
    headers = {"authtoken": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"}
    input_data = f'''{{
        "request": {{
            "udf_fields": {{
                "udf_sline_11101": "{contract_name}"
            }}
        }}
    }}'''
    data = {'input_data': input_data}
    response = requests.put(url, headers=headers, data=data, verify=False)

    if response.status_code == 200:
        print(f"Request {request_id} updated successfully with contract name: {contract_name}")
    else:
        print(f"Error updating request {request_id}: {response.status_code} - {response.text}")

# Step 1: Load contracts info from Excel
contracts_info = load_contracts_info('contracts_info.xlsx')

# Step 2: Fetch all requests
requests_list = fetch_requests()

# Step 3: For each request, get its details and extract assets and account name
for request in requests_list:
    request_id = request.get("id")
    request_details = fetch_request_details(request_id)

    # Extract assets and account name
    assets = request_details.get("assets", [])
    account_name = request_details.get("account", {}).get("name", "No account found")

    # Print details
    print(f"Request ID: {request_id}")
    print(f"  Account Name: {account_name}")

    # Check if account name exists in contracts_info
    if account_name in contracts_info['Account Name'].values:
        # Iterate over assets to check against the contracts_info
        for asset in assets:
            asset_name = asset.get("name").strip()  # Clean asset name
            print(f"  Checking asset: {asset_name}")  # Display the asset being checked
            
            # Standardize asset name to lowercase for comparison
            matching_rows = contracts_info[
                (contracts_info['Account Name'] == account_name) &
                (contracts_info['Asset Name'].str.lower() == asset_name.lower())
            ]

            # If there is a matching row, update the request
            if not matching_rows.empty:
                contract_name = matching_rows['Contract Name'].values[0]  # Get the contract name
                print(f"  Match found: {contract_name}")
                # Update request with the contract name
                update_request(request_id, contract_name)
                break  # Stop checking once we find a match
        else:
            print(f"  No match found. Assets in request: {[asset.get('name') for asset in assets]}")
    else:
        print("  Account not found in contracts_info.")
