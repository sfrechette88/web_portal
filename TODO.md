## Liste TODO

- [X] Ajouter un `.gitignore` pour exclure les fichiers temporaires et l’environnement virtuel  
- [X] Supprimer ou fusionner `simple_app.py` et stabiliser l’architecture modulaire
        --> Création d'un dossier 'debug' et déplacement du fichier 'simple_app.py' dedans.
- [X] Mettre en place Flask-Migrate
  - ajouter `Flask-Migrate` à requirements.txt
  - dans `app/__init__.py` :
    - `from flask_migrate import Migrate`
    - `migrate = Migrate()`
    - `migrate.init_app(app, db)`
  - à la racine :
    - `export FLASK_APP=run.py`
    - `flask db init`
    - `flask db migrate -m "Initial"`
    - `flask db upgrade`
- [ ] Externaliser la configuration (SECRET_KEY, DATABASE_URI) dans un fichier `.env`  
- [ ] Changement de DB pour MySQL...
- [ ] Rédiger un `README.md` détaillant l’installation, la configuration et le déploiement  
- [ ] Écrire des tests unitaires (pytest) pour les modèles, formulaires et routes critiques  
- [ ] Améliorer l’UI/UX : navbar commune, catégories de flash, intégration de Bootstrap  

## Liste de suivi (Suivi)

| Tâche                                | Statut     | Commentaires                               |
| ------------------------------------ | ---------- | ------------------------------------------ |
| Ajouter un `.gitignore`              | En attente | À créer dans la racine du repo             |
| Unifier app (fusion `simple_app.py`) | En attente | Choisir la version blueprint               |
| Mise en place Flask-Migrate          | En attente | Installer & configurer Alembic             |
| Externaliser config (`.env`)         | En attente | Utiliser `python-dotenv`                   |
| Rédaction `README.md`                | En attente | Expliquer prérequis, installation et usage |
| Écriture de tests unitaires          | En attente | Cibler modèles, formulaires et routes clés |
| UI/UX (navbar & Bootstrap)           | En attente | Créer un layout de base                    |
