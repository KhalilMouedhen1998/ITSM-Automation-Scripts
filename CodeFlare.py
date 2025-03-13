import requests
import json

# URL pour l'API des demandes de tickets
url = "https://192.168.10.1/api/v3/requests/{request_id}"
headers = {"authtoken": "906B26D6-70E5-4B71-BAF8-DCD21143B0EE"}

# URL de l'API des assets pour récupérer l'ID de l'asset par nom
assets_url = "https://192.168.10.1/api/v3/assets"
assets_headers = {"authtoken": "906B26D6-70E5-4B71-BAF8-DCD21143B0EE"}

input_data = '''{
    "list_info": {
        "row_count": 100;
        "start_index": 0
    }
}'''
params = {'input_data': input_data}

# Fonction pour récupérer l'ID de l'asset à partir du nom de l'asset
def get_asset_id_by_name(asset_name):
    row_count = 5
    start_index = 0
    total_assets_found = 0
    missing_name_assets = []  # Pour suivre les assets sans nom

    while True:
        input_data = f'''{{
            "list_info": {{
                "row_count": {row_count},
                "start_index": {start_index}
            }}
        }}'''
        params = {'input_data': input_data}
        response = requests.get(assets_url, headers=assets_headers, params=params, verify=False)

        if response.status_code != 200:
            print("Erreur lors de la récupération des assets :", response.status_code)
            return None
        
        data = response.json()
        assets = data.get('assets', [])
        total_assets_found += len(assets)

        for asset in assets:
            name = asset.get('name')
            if name is None or name.strip() == "":
                missing_name_assets.append(asset.get('id'))  # Ajouter l'ID de l'asset sans nom
            else:
                print(f"Nom de l'asset: {name}, ID de l'asset: {asset.get('id')}")
                if name == asset_name:
                    return asset.get('id')
        
        start_index += row_count
        if not assets:
            break

    print(f"Nombre total d'assets récupérés : {total_assets_found}")
    print(f"Assets sans nom détecté : {missing_name_assets}")
    return None


# Fonction pour mettre à jour le champ udf_sline_11402 de l'asset
def update_asset_udf(asset_id, udf_value):
    update_url = f"https://192.168.10.1/api/v3/assets/{asset_id}"
    headers = {"authtoken": "906B26D6-70E5-4B71-BAF8-DCD21143B0EE"}
    input_data = {
        "asset": {
            "udf_fields": {
                "udf_sline_11402": udf_value
            }
        }
    }
    data = {'input_data': json.dumps(input_data)}
    response = requests.put(update_url, headers=headers, data=data, verify=False)
    if response.status_code == 200:
        print(f"Asset ID {asset_id} mis à jour avec succès!")
    else:
        print(f"Erreur lors de la mise à jour de l'asset ID {asset_id}. Code HTTP: {response.status_code}")

# Récupération des demandes de tickets
response = requests.get("https://192.168.10.1/api/v3/requests", headers=headers, params=params, verify=False)

# Vérification du succès de la requête
if response.status_code == 200:
    data = response.json()
    all_requests = data.get('requests', [])

    # Filtrage des demandes par template (Upgrade Hardware ou Upgrade Software)
    template_requests = [
        req for req in all_requests if req.get('template', {}).get('name') in ["Upgrade Hardware", "Upgrade Software"]
    ]

    # Extraction des détails de chaque ticket filtré
    extracted_data = []
    for req in template_requests:
        request_id = req.get('id')
        if request_id:
            detailed_url = url.format(request_id=request_id)
            detailed_response = requests.get(detailed_url, headers=headers, verify=False)

            if detailed_response.status_code == 200:
                detailed_data = detailed_response.json()

                # Extraction du champ udf_sline_11701
                udf_field = detailed_data.get('request', {}).get('udf_fields', {}).get('udf_sline_11701', "No UDF Value")

                # Extraction du nom de l'asset
                asset_name = ""
                asset_id = None
                if detailed_data.get('request', {}).get('assets'):
                    asset_name = detailed_data['request']['assets'][0].get('name', "No Asset Name")
                    # Recherche de l'ID de l'asset correspondant
                    asset_id = get_asset_id_by_name(asset_name)

                # Ajouter les données extraites si l'ID de l'asset a été trouvé
                if asset_id:
                    extracted_data.append({
                        "request_id": request_id,  # Afficher l'ID du ticket
                        "udf_sline_11701": udf_field,
                        "asset_name": asset_name,
                        "asset_id": asset_id
                    })

                    # Mise à jour du champ udf_sline_11402 dans l'asset
                    update_asset_udf(asset_id, udf_field)

                else:
                    print(f"Asset ID non trouvé pour l'asset {asset_name} dans le ticket {request_id}.")
            else:
                print(f"Échec de la récupération des détails pour le ticket ID {request_id}. Code HTTP: {detailed_response.status_code}")
    
    # Afficher les données extraites
    print("Extracted Data:", json.dumps(extracted_data, indent=4))
else:
    print(f"Échec de la récupération des demandes. Code HTTP: {response.status_code}")
