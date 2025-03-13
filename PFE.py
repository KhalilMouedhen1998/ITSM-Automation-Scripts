import pandas as pd
from fuzzywuzzy import process

# Lire le fichier Excel
df = pd.read_excel("PARTS_COMPATIBILITY_REPORT.xlsx")

# Demander la plateforme et le PN
PLATFORM = input("Entrez la plateforme (ex: VNXE1600): ").lower()  # On normalise l'entrée en minuscules
pn = input("Entrez le Part Number: ")

# Normalisation de la colonne PLATFORM en minuscules pour une recherche insensible à la casse
df['PLATFORM'] = df['PLATFORM'].str.lower()

# Utilisation de fuzzy matching pour trouver la meilleure correspondance de la plateforme
best_match_platform = process.extractOne(PLATFORM, df['PLATFORM'])

# Vérifier si une correspondance suffisante a été trouvée pour la plateforme
if best_match_platform and best_match_platform[1] > 80:  # Seuil de confiance à 80%
    matched_platform = best_match_platform[0]
    print(f"Plateforme correspondante trouvée : {matched_platform}")

    # Utilisation de fuzzy matching pour trouver la meilleure correspondance du Part Number
    best_match_pn = process.extractOne(pn, df['PART NUMBER'].astype(str))  # Conversion en chaîne pour le PN

    # Vérifier si une correspondance suffisante a été trouvée pour le PN
    if best_match_pn and best_match_pn[1] > 80:  # Seuil de confiance à 80%
        matched_pn = best_match_pn[0]
        print(f"Part Number correspondant trouvé : {matched_pn}")

        # Filtrer les données en utilisant la plateforme et le Part Number correspondants
        result = df[(df['PLATFORM'] == matched_platform) & (df['PART NUMBER'] == matched_pn)]

        # Vérifier si des résultats sont trouvés
        if not result.empty:
            compatible_pn = result[['SUBS NUMBER', 'PART DESCRIPTION']]  # Affichage du PN et de sa description
            print("Les PN compatibles et leurs descriptions sont :")
            print(compatible_pn)
        else:
            print("Aucune correspondance trouvée pour le Part Number.")
    else:
        print("Aucune correspondance satisfaisante trouvée pour le Part Number.")
else:
    print("Aucune correspondance satisfaisante trouvée pour la plateforme.")
