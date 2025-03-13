import subprocess

scripts = ["HJpROD.py", "HJCorrectionpp.py", "SoldeHJ.py"]

for script in scripts:
    try:
        print(f"Lancement de {script}...")
        subprocess.run(["python", script], check=True)
        print(f"{script} terminé avec succès.\n")
    except subprocess.CalledProcessError as e:
        print(f"Erreur lors de l'exécution de {script}: {e}")
        break  # Arrête l'exécution si un script échoue
