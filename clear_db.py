#!/usr/bin/env python3
from app import create_app, db

app = create_app()

with app.app_context():
    confirm = input("⚠️  Cette opération va SUPPRIMER toutes les tables de la base. Continuer ? (oui/non) : ")
    if confirm.lower() != "oui":
        print("Opération annulée.")
        exit(0)

    db.drop_all()
    print("🗑️  Toutes les tables ont été supprimées.")

    # Si tu veux recréer les tables après :
    recreate = input("Voulez-vous recréer les tables tout de suite ? (oui/non) : ")
    if recreate.lower() == "oui":
        db.create_all()
        print("📦  Toutes les tables ont été recréées (vides).")

print("✅ Terminé.")
