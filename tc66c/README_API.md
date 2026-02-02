# TC66C API Server & Dashboard

Serveur API REST avec interface web pour visualiser les données du TC66C en temps réel.

## Fonctionnalités

- **API REST** : Récupération des données sur des périodes configurables
- **Stockage flexible** : Rétention configurable des données (défaut : 10 minutes)
- **Dashboard Web** : Interface de visualisation avec graphiques en temps réel
- **Graphiques interactifs** : Courbes de courant et puissance en direct
- **Statut en temps réel** : Affichage des valeurs actuelles et statistiques
- **Format flexible** : Requêtes par période (5m, 1h, 30s, etc.)

## Installation

```bash
# Installer les dépendances
pip install -r requirements.txt
```

## Lancement

```bash
# Démarrer le serveur sur le port 5000 (défaut)
python api_server.py

# Ou spécifier un port personnalisé
python api_server.py 8000
```

Le serveur démarre avec :
```
Démarrage du serveur API sur le port 5000...
Port TC66C: /dev/ttyACM0
Intervalle de polling: 1.0s
Rétention des données: 10min
```

## Interface Web

Accédez à la dashboard via votre navigateur :

```
http://localhost:5000
```

##  API Endpoints

### 1. Récupérer les données sur une période

```
GET /api/data/<periode>
```

**Formats de période :**
- `5m` : 5 dernières minutes
- `1h` : 1 dernière heure  
- `30s` : 30 dernières secondes
- `Nm` : N minutes
- `Nh` : N heures
- `Ns` : N secondes

**Exemple :**
```bash
curl http://localhost:5000/api/data/5m
```

**Réponse :**
```json
{
  "period": "5m",
  "count": 42,
  "start_time": "2026-01-19T14:25:00.000000",
  "end_time": "2026-01-19T14:30:00.000000",
  "data": [
    {
      "timestamp": "2026-01-19T14:25:12.123456",
      "voltage": 5.00,
      "current": 0.250,
      "power": 1.25
    },
    ...
  ]
}
```

### 2. Obtenir le dernier point de données

```
GET /api/data/latest
```

**Réponse :**
```json
{
  "timestamp": "2026-01-19T14:30:00.123456",
  "voltage": 5.00,
  "current": 0.250,
  "power": 1.25
}
```

### 3. Statistiques sur une période

```
GET /api/stats/<periode>
```

**Exemple :**
```bash
curl http://localhost:5000/api/stats/1h
```

**Réponse :**
```json
{
  "period": "1h",
  "sample_count": 600,
  "voltage": {
    "min": 4.95,
    "max": 5.05,
    "avg": 5.00
  },
  "current": {
    "min": 0.100,
    "max": 0.500,
    "avg": 0.250
  },
  "power": {
    "min": 0.50,
    "max": 2.50,
    "avg": 1.25
  }
}
```

### 4. Statut du serveur

```
GET /api/status
```

**Réponse :**
```json
{
  "running": true,
  "data_count": 342,
  "oldest_data": "2026-01-19T14:20:00.000000",
  "newest_data": "2026-01-19T14:30:00.000000",
  "retention_minutes": 10,
  "polling_interval": 1.0
}
```

### 5. Configuration

**Afficher la configuration :**
```bash
curl http://localhost:5000/api/config
```

**Modifier la configuration :**
```bash
curl -X POST http://localhost:5000/api/config \
  -H "Content-Type: application/json" \
  -d '{"port": "/dev/ttyACM1", "data_retention_minutes": 30, "polling_interval": 2.0}'
```

##  Configuration

Modifiez le dictionnaire `CONFIG` dans `api_server.py` :

```python
CONFIG = {
    'port': '/dev/ttyACM0',           # Port du TC66C
    'polling_interval': 1.0,          # Intervalle de lecture en secondes
    'data_retention_minutes': 10,     # Durée de rétention des données
}
```

### Paramètres

| Paramètre | Type | Défaut | Description |
|-----------|------|--------|-------------|
| `port` | str | `/dev/ttyACM0` | Port série du TC66C |
| `polling_interval` | float | 1.0 | Intervalle entre les lectures (secondes) |
| `data_retention_minutes` | int | 10 | Durée de rétention des données (minutes) |

##  Format des données

Chaque point de données contient :

```json
{
  "timestamp": "2026-01-19T14:30:00.123456",
  "voltage": 5.00,              // Tension en volts
  "current": 0.250,             // Courant en ampères
  "power": 1.25                 // Puissance en watts
}
```


##  Dépannage

### Erreur : "failed to open:/dev/ttyACM0"

Le port spécifié n'existe pas. Vérifiez la connexion du TC66C et ajustez `CONFIG['port']`.

```bash
# Lister les ports disponibles
ls /dev/tty*
```

