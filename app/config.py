import os
from pathlib import Path
from dotenv import load_dotenv

# On définit la racine du projet (un cran au-dessus de app/)
BASE_DIR = Path(__file__).resolve().parent.parent

# Charge le fichier .env situé à la racine du projet
load_dotenv(dotenv_path=BASE_DIR / '.env')

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key-change-in-production')

    # Récupère DATABASE_URI depuis .env, sinon sqlite en instance/
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URI',
        # chemin vers web_portal.db dans le dossier instance/
        f"sqlite:///{BASE_DIR / 'instance' / 'web_portal.db'}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # ---- Configuration des cookies de session ----
    # Domaine : None → prend automatiquement le nom du site appelant
    SESSION_COOKIE_DOMAIN = None
    # Chemin : racine de l’app
    SESSION_COOKIE_PATH = '/'
    # Secure : False si vous n’êtes pas encore en HTTPS en prod
    SESSION_COOKIE_SECURE = False
    # SameSite : 'Lax' ou 'Strict' selon vos besoins
    SESSION_COOKIE_SAMESITE = 'Lax'