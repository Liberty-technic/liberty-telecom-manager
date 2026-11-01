# LIBERTY TELECOM MANAGER — prototype initial

## Ce qui fonctionne dans ce prototype
- Création de compte et connexion.
- Espaces clients séparés (tickets et routeurs par compte).
- Tableau de bord.
- Offres Basic (5 000), Professionnel (10 000), Entreprise (15 000 FCFA/mois), en mode démonstration.
- Génération de tickets et export CSV.
- Enregistrement des routeurs MikroTik.
- Téléchargement d'un script HotSpot RouterOS v7 de base, à adapter.

## Démarrage sur ordinateur
1. Installer Python 3.11 ou plus récent.
2. Dans ce dossier, ouvrir un terminal :
   `python -m venv .venv`
3. Activer l'environnement :
   Windows : `.venv\\Scripts\\activate`
   Linux : `source .venv/bin/activate`
4. Installer : `pip install -r requirements.txt`
5. Démarrer : `python app.py`
6. Ouvrir `http://127.0.0.1:5000`

## Déploiement Docker
`docker compose up --build -d`
Puis ouvrir `http://localhost:5000`.

## IMPORTANT — avant vente au public
Ce paquet est un prototype fonctionnel de départ, pas une plateforme de production.
- Le paiement Moov Money/Airtel Money est simulé : aucun argent réel n'est encaissé.
- L'activation d'offre est une démonstration de 30 jours.
- La configuration distante automatique du MikroTik n'est pas encore branchée.
- Le script fourni est un exemple RouterOS v7 non destructif, mais doit être adapté à chaque réseau et vérifié avant import.
- `session-timeout` limite une session, ce n'est pas une expiration calendaire garantie depuis la première connexion.
- Il faut ajouter HTTPS, PostgreSQL, protection CSRF, limitation de tentatives, récupération de mot de passe, journalisation, sauvegardes et stockage chiffré des secrets.
- Pour le MikroTik, préférer un agent local sortant ou VPN, jamais une API exposée directement à Internet.
- Il faut les accès marchands/API de Moov Money et Airtel Money pour activer les paiements réels.
- L'impression PDF/thermique, QR code et APK Android restent à développer.

## Identité et tarifs retenus
LIBERTY TELECOM MANAGER — FCFA — abonnements mensuels : 5 000 / 10 000 / 15 000.
