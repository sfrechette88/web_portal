import os
from pathlib import Path
from dotenv import load_dotenv

# On définit la racine du projet (un cran au-dessus de app/)
BASE_DIR = Path(__file__).resolve().parent.parent

# 🔹 Dossier instance/ pour la DB locale
INSTANCE_DIR = BASE_DIR / "instance"
INSTANCE_DIR.mkdir(exist_ok=True)  # <-- crée le dossier au besoin

# 🔹 Chemin absolu vers la DB SQLite locale
DB_PATH = INSTANCE_DIR / "web_portal.db"

# Charge le fichier .env situé à la racine du projet
load_dotenv(dotenv_path=BASE_DIR / ".env")


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-key-change-in-production")

    # Récupère DATABASE_URI depuis .env, sinon sqlite en instance/
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URI",
        f"sqlite:///{DB_PATH.as_posix()}",  # <-- chemin propre, même sous Windows
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ---- Configuration des cookies de session ----
    SESSION_COOKIE_DOMAIN = None
    SESSION_COOKIE_PATH = "/"
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_SAMESITE = "Lax"
