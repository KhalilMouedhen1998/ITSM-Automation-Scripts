import pandas as pd
import numpy as np
import requests
import json
import urllib3
from datetime import datetime

# Désactiver les avertissements SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuration de l'API
BASE_URL = "/api/v3/requests"
HEADERS = {"authtoken": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"}

# Chemins des fichiers
COMPETENCE_MATRIX_PATH = r"matrice_categories_INFRA.xlsx"
TICKET_ASSIGNMENTS_PATH = r"Procédure d'affectation des tickets 2025.xlsx"

# Noms des techniciens
TECH_NAMES = ['Catégorie', 'Sous-catégorie', '', '', '', '', '', '']

def load_competence_matrix():
    """Charger la matrice de compétences"""
    try:
        df = pd.read_excel(COMPETENCE_MATRIX_PATH, sheet_name=0)
        df.columns = TECH_NAMES
        df['Catégorie'] = df['Catégorie'].fillna('').str.strip()
        df['Sous-catégorie'] = df['Sous-catégorie'].fillna('').str.strip()
        return df
    except Exception as e:
        print(f"Erreur de chargement de la matrice de compétences : {e}")
        return None

def load_ticket_assignments():
    """Charger les affectations de tickets"""
    try:
        ticket_df = pd.read_excel(
            TICKET_ASSIGNMENTS_PATH,
            sheet_name='Incidents L1 & L2',
            usecols="A:H",
            header=None
        )
        required_rows = [4, 8, 9, 10, 11, 12]
        ticket_df = ticket_df.iloc[required_rows].copy()
        ticket_df = ticket_df.reset_index(drop=True)
        return ticket_df
    except Exception as e:
        print(f"Erreur de chargement des affectations de tickets : {e}")
        return None

def find_technicians_for_category_subcategory(df, category, subcategory):
    """Trouver les techniciens compétents pour une catégorie/sous-catégorie"""
    category = str(category).strip()
    subcategory = str(subcategory).strip()
    
    filtered_rows = df[
        (df['Catégorie'].str.strip().str.lower() == category.lower()) | 
        (df['Sous-catégorie'].str.strip().str.lower() == subcategory.lower())
    ]
    
    filtered_row = filtered_rows[
        filtered_rows['Sous-catégorie'].str.strip().str.lower() == subcategory.lower()
    ]
    
    if filtered_row.empty:
        return {}
    
    tech_columns = TECH_NAMES[2:]
    technicians = {}
    row_index = filtered_row.index[0]
    
    for tech in tech_columns:
        cell_value = df.at[row_index, tech]
        if pd.notna(cell_value):
            cell_str = str(cell_value).strip().upper()
            if cell_str == 'X':
                technicians[tech] = 'X'
    
    return technicians

def count_tickets_per_technician(ticket_df):
    """Compter les tickets par technicien"""
    tech_columns = TECH_NAMES[2:]
    ticket_counts = {tech: 0 for tech in tech_columns}
    
    position_mapping = {
        0: '',
        1: '',
        2: '',
        3: '',
        4: '',
        5: ''
    }
    
    for index, row in ticket_df.iterrows():
        if index in position_mapping:
            tech_name = position_mapping[index]
            values = [str(val).strip() for val in row.iloc[1:] if pd.notna(val) and str(val).strip() != '']
            count = len(values)
            ticket_counts[tech_name] = count
    
    return ticket_counts

def get_technician_recommendation(competence_techs, ticket_counts):
    """Recommander le technicien avec la compétence et le moins de tickets"""
    if not competence_techs:
        return None
        
    filtered_ticket_counts = {
        tech: count for tech, count in ticket_counts.items() 
        if tech in competence_techs
    }
    
    if not filtered_ticket_counts:
        return None
    
    recommended_tech = min(filtered_ticket_counts, key=filtered_ticket_counts.get)
    return recommended_tech

def get_tickets_from_api():
    """Récupérer les tickets depuis l'API"""
    input_data = json.dumps({"list_info": {"row_count": 10, "start_index": 1}})
    params = {"input_data": input_data}
    
    try:
        response = requests.get(BASE_URL, headers=HEADERS, params=params, verify=False)
        response.raise_for_status()
        return response.json().get("requests", [])
    except requests.RequestException as e:
        print(f"Erreur lors de la récupération des demandes : {e}")
        return []

def get_ticket_details(request_id):
    """Récupérer les détails d'un ticket"""
    details_url = f"{BASE_URL}/{request_id}"
    try:
        response = requests.get(details_url, headers=HEADERS, verify=False)
        response.raise_for_status()
        return response.json().get("request", {})
    except requests.RequestException as e:
        print(f"Erreur lors de la récupération des détails pour la requête {request_id} : {e}")
        return None

def main():
    print("Chargement des données...")
    competence_df = load_competence_matrix()
    ticket_df = load_ticket_assignments()
    
    if competence_df is None or ticket_df is None:
        print("Erreur: Impossible de charger les données requises.")
        return
    
    print("Récupération des tickets depuis l'API...")
    tickets = get_tickets_from_api()
    
    if not tickets:
        print("Aucun ticket trouvé.")
        return
    
    print("\nAnalyse des tickets escaladés...\n")
    print("-" * 80)
    
    for ticket in tickets:
        request_id = ticket.get("id")
        if not request_id:
            continue
            
        details = get_ticket_details(request_id)
        if not details:
            continue
            
        # Extraction des données du ticket
        created_time = details.get("created_time", {}).get("display_value", "N/A")
        category = details.get("category", {}).get("name", "N/A")
        subcategory_data = details.get("subcategory")
        subcategory = subcategory_data["name"] if isinstance(subcategory_data, dict) else "N/A"
        status_data = details.get("status")
        status = status_data["name"] if isinstance(status_data, dict) else "N/A"
        
        # Ne traiter que les tickets avec le statut "Escalader"
        if status.lower() != "escalated":
            continue
            
        # Trouver le technicien approprié
        competent_techs = find_technicians_for_category_subcategory(competence_df, category, subcategory)
        ticket_counts = count_tickets_per_technician(ticket_df)
        recommended_tech = get_technician_recommendation(competent_techs, ticket_counts)
        
        print(f"Ticket ID: {request_id}")
        print(f"Date de création: {created_time}")
        if recommended_tech:
            print(f"Technicien recommandé: {recommended_tech}")
        else:
            print("Aucun technicien disponible avec les compétences requises")
        print("-" * 80)

if __name__ == "__main__":
    main()
