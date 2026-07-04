# Supprime le fichier de base de données de test s'il a été créé à la racine
Remove-Item -ErrorAction Ignore test.db, oxygen.db

# Supprime les dossiers de cache
Remove-Item -Recurse -Force -ErrorAction Ignore .pytest_cache

# Ajoute et tente le commit
git add .
git commit -m "main.py stable"
