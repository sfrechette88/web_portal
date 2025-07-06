#!/usr/bin/env python3
import sys
import os

# Ajouter le répertoire de l'application au chemin Python
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Charger les variables d'environnement depuis .env
from dotenv import load_dotenv
# Charger .env depuis le même répertoire que ce fichier wsgi
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env'))

# Importer l'application
from run import app as application