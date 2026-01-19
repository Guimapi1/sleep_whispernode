#!/usr/bin/env python3
"""
API Server pour TC66C
Permet de requêter les données des N dernières minutes via une API REST
"""

from flask import Flask, jsonify
from datetime import datetime, timedelta
from threading import Thread, Lock
from collections import deque
import re
from time import sleep
from tc66c.TC66C import TC66C

app = Flask(__name__)

# Configuration
CONFIG = {
    'port': '/dev/ttyACM0',
    'polling_interval': 1.0,  # secondes entre chaque lecture
    'data_retention_minutes': 10,  # nombre de minutes de rétention des données
}

# Stockage des données avec timestamp
data_storage = deque()
data_lock = Lock()
is_running = False
tc66c = None


class DataPoint:
    """Représente un point de données avec timestamp"""
    def __init__(self, poll_data):
        self.timestamp = datetime.now()
        self.data = poll_data
    
    def to_dict(self):
        return {
            'timestamp': self.timestamp.isoformat(),
            'voltage': self.data.Volt,
            'current': self.data.Current,
            'power': self.data.Power,
            'resistance': self.data.Resistance,
            'temperature': self.data.Temp,
            'mah_g0': self.data.G0_mAh,
            'mwh_g0': self.data.G0_mWh,
            'mah_g1': self.data.G1_mAh,
            'mwh_g1': self.data.G1_mWh,
        }


def cleanup_old_data():
    """Supprime les données plus anciennes que la période de rétention"""
    cutoff_time = datetime.now() - timedelta(minutes=CONFIG['data_retention_minutes'])
    
    with data_lock:
        while data_storage and data_storage[0].timestamp < cutoff_time:
            data_storage.popleft()


def polling_thread():
    """Thread qui récupère les données du TC66C à intervalles réguliers"""
    global tc66c
    
    try:
        tc66c = TC66C(CONFIG['port'])
    except Exception as e:
        print(f"Erreur d'initialisation TC66C: {e}")
        return
    
    while is_running:
        try:
            poll_data = tc66c.Poll()
            if poll_data:
                data_point = DataPoint(poll_data)
                with data_lock:
                    data_storage.append(data_point)
                
                # Nettoyage périodique (toutes les 10 lectures)
                if len(data_storage) % 10 == 0:
                    cleanup_old_data()
            
            sleep(CONFIG['polling_interval'])
        except Exception as e:
            print(f"Erreur lors du polling: {e}")
            sleep(CONFIG['polling_interval'])


def parse_time_param(time_str):
    """
    Parse un paramètre de temps comme '5m', '1h', '30s'
    Retourne un timedelta
    """
    pattern = r'^(\d+)([smh])$'
    match = re.match(pattern, time_str)
    
    if not match:
        return None
    
    value, unit = match.groups()
    value = int(value)
    
    if unit == 's':
        return timedelta(seconds=value)
    elif unit == 'm':
        return timedelta(minutes=value)
    elif unit == 'h':
        return timedelta(hours=value)
    
    return None


@app.route('/api/data/<time_period>', methods=['GET'])
def get_data(time_period):
    """
    Retourne les données sur une période donnée
    
    Exemples:
    /api/data/5m     -> 5 dernières minutes
    /api/data/1h     -> 1 dernière heure
    /api/data/30s    -> 30 dernières secondes
    """
    # Parse le paramètre de temps
    delta = parse_time_param(time_period)
    
    if delta is None:
        return jsonify({
            'error': 'Format invalide',
            'message': 'Utilisez le format: Nm, Nh ou Ns (ex: 5m, 1h, 30s)'
        }), 400
    
    cutoff_time = datetime.now() - delta
    
    with data_lock:
        # Filtre les données dans la période
        filtered_data = [
            point.to_dict() 
            for point in data_storage 
            if point.timestamp >= cutoff_time
        ]
    
    return jsonify({
        'period': time_period,
        'count': len(filtered_data),
        'start_time': cutoff_time.isoformat(),
        'end_time': datetime.now().isoformat(),
        'data': filtered_data
    }), 200


# @app.route('/api/data/latest', methods=['GET'])
# def get_latest():
    """Retourne le dernier point de données"""
    with data_lock:
        if not data_storage:
            return jsonify({
                'error': 'Pas de données disponibles'
            }), 404
        
        latest = data_storage[-1].to_dict()
    
    return jsonify(latest), 200


# @app.route('/api/stats/<time_period>', methods=['GET'])
# def get_stats(time_period):
#     """
#     Retourne les statistiques (min, max, moyenne) sur une période
#     """
#     delta = parse_time_param(time_period)
    
#     if delta is None:
#         return jsonify({
#             'error': 'Format invalide',
#             'message': 'Utilisez le format: Nm, Nh ou Ns (ex: 5m, 1h, 30s)'
#         }), 400
    
#     cutoff_time = datetime.now() - delta
    
#     with data_lock:
#         filtered_data = [
#             point 
#             for point in data_storage 
#             if point.timestamp >= cutoff_time
#         ]
    
#     if not filtered_data:
#         return jsonify({
#             'error': 'Pas de données pour cette période'
#         }), 404
    
#     # Calcul des statistiques
#     voltages = [p.data.Volt for p in filtered_data]
#     currents = [p.data.Current for p in filtered_data]
#     powers = [p.data.Power for p in filtered_data]
    
#     stats = {
#         'period': time_period,
#         'sample_count': len(filtered_data),
#         'voltage': {
#             'min': min(voltages),
#             'max': max(voltages),
#             'avg': sum(voltages) / len(voltages)
#         },
#         'current': {
#             'min': min(currents),
#             'max': max(currents),
#             'avg': sum(currents) / len(currents)
#         },
#         'power': {
#             'min': min(powers),
#             'max': max(powers),
#             'avg': sum(powers) / len(powers)
#         }
#     }
    
#     return jsonify(stats), 200


@app.route('/api/config', methods=['GET', 'POST'])
def config():
    """Affiche ou modifie la configuration"""
    if request.method == 'GET':
        return jsonify(CONFIG), 200
    
    # POST - modifier la configuration
    from flask import request
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Pas de données'}), 400
    
    # Mise à jour sécurisée des paramètres
    if 'polling_interval' in data:
        CONFIG['polling_interval'] = float(data['polling_interval'])
    
    if 'data_retention_minutes' in data:
        CONFIG['data_retention_minutes'] = int(data['data_retention_minutes'])
        cleanup_old_data()
    
    return jsonify({
        'message': 'Configuration mise à jour',
        'config': CONFIG
    }), 200


# @app.route('/api/status', methods=['GET'])
# def status():
#     """Affiche le statut du serveur et du système de stockage"""
#     with data_lock:
#         data_count = len(data_storage)
    
#     oldest = None
#     newest = None
#     if data_storage:
#         with data_lock:
#             oldest = data_storage[0].timestamp.isoformat()
#             newest = data_storage[-1].timestamp.isoformat()
    
#     return jsonify({
#         'running': is_running,
#         'data_count': data_count,
#         'oldest_data': oldest,
#         'newest_data': newest,
#         'retention_minutes': CONFIG['data_retention_minutes'],
#         'polling_interval': CONFIG['polling_interval']
#     }), 200


def start_server(port=5000, debug=False):
    """Démarre le serveur API"""
    global is_running
    
    is_running = True
    
    # Démarre le thread de polling
    polling_t = Thread(target=polling_thread, daemon=True)
    polling_t.start()
    
    print(f"Démarrage du serveur API sur le port {port}...")
    print(f"Port TC66C: {CONFIG['port']}")
    print(f"Intervalle de polling: {CONFIG['polling_interval']}s")
    print(f"Rétention des données: {CONFIG['data_retention_minutes']}min")
    
    try:
        app.run(host='0.0.0.0', port=port, debug=debug)
    except KeyboardInterrupt:
        print("\nArrêt du serveur...")
        is_running = False


if __name__ == '__main__':
    import sys
    
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
    start_server(port=port)
