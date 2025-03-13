import pandas as pd

def analyser_charge_tickets(fichier_excel, feuille):
    """
    Analyse le nombre de tickets assignés à chaque technicien
    
    Parameters:
    fichier_excel (str): Chemin vers le fichier Excel
    feuille (str): Nom de la feuille à analyser
    
    Returns:
    tuple: (technicien avec le moins de tickets, nombre de tickets)
    """
    try:
        # Lecture du fichier Excel
        df = pd.read_excel(fichier_excel, sheet_name=feuille)
        
        # Sélection des lignes des techniciens (29 à 32)
        techs_df = df.iloc[19:22]  # Index 0-based donc 28-31 pour lignes 29-32
        
        # Dictionnaire pour stocker le nombre de tickets par technicien
        charge_techs = {}
        
        # Pour chaque technicien
        for index, row in techs_df.iterrows():
            # Le nom du technicien est dans la colonne A
            tech_name = row.iloc[0]
            # Compter le nombre de cellules non vides (exclure la première colonne qui contient le nom)
            nb_tickets = row.iloc[1:].notna().sum()
            charge_techs[tech_name] = nb_tickets
        
        # Trouver le technicien avec le moins de tickets
        tech_min = min(charge_techs.items(), key=lambda x: x[1])
        
        return tech_min
        
    except Exception as e:
        return f"Erreur lors de l'analyse : {str(e)}"

# Exemple d'utilisation
fichier = "Procédure d'affectation des tickets 2025.xlsx"
tech, nb_tickets = analyser_charge_tickets(fichier, "Incidents Cloud")
print(f"Le technicien {tech} a le moins de tickets avec {nb_tickets} tickets.")