## Lancer l'affichage en temps réel
Après avoir cloner le dépôt, effectuez les commandes suivantes :
1. Créer un environnement virtuel : `python3 -m venv .venv` (sur macOS/Linux) et  `py -3 -m venv .venv` (sur Windows)
2. Activer l'environnement : `. .venv/bin/activate` (sur macOS/Linux) et  `.venv\Scripts\activate` (sur Windows)
3. Installer les dependances necessaire : `pip install -r requirements.txt `
4. Lancer le script : `cd tc66c && python3 plot_realtime.py`

Au besoin, pensez à utiliser la commande `pio device list --serial` dans le terminal pio pour trouver sur quel port est connecté votre tc66c