#!/usr/bin/env python3
"""
API Server pour TC66C
Permet de requêter les données des N dernières minutes via une API REST
"""

from flask import Flask, jsonify, request
from datetime import datetime, timedelta
from threading import Thread, Lock
from collections import deque
import re
from time import sleep
from TC66C import TC66C

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


@app.route('/api/data/latest', methods=['GET'])
def get_latest():
    """Retourne le dernier point de données"""
    with data_lock:
        if not data_storage:
            return jsonify({
                'error': 'Pas de données disponibles'
            }), 404
        
        latest = data_storage[-1].to_dict()
    
    return jsonify(latest), 200


@app.route('/api/stats/<time_period>', methods=['GET'])
def get_stats(time_period):
    """
    Retourne les statistiques (min, max, moyenne) sur une période
    """
    delta = parse_time_param(time_period)
    
    if delta is None:
        return jsonify({
            'error': 'Format invalide',
            'message': 'Utilisez le format: Nm, Nh ou Ns (ex: 5m, 1h, 30s)'
        }), 400
    
    cutoff_time = datetime.now() - delta
    
    with data_lock:
        filtered_data = [
            point 
            for point in data_storage 
            if point.timestamp >= cutoff_time
        ]
    
    if not filtered_data:
        return jsonify({
            'error': 'Pas de données pour cette période'
        }), 404
    
    # Calcul des statistiques
    voltages = [p.data.Volt for p in filtered_data]
    currents = [p.data.Current for p in filtered_data]
    powers = [p.data.Power for p in filtered_data]
    
    stats = {
        'period': time_period,
        'sample_count': len(filtered_data),
        'voltage': {
            'min': min(voltages),
            'max': max(voltages),
            'avg': sum(voltages) / len(voltages)
        },
        'current': {
            'min': min(currents),
            'max': max(currents),
            'avg': sum(currents) / len(currents)
        },
        'power': {
            'min': min(powers),
            'max': max(powers),
            'avg': sum(powers) / len(powers)
        }
    }
    
    return jsonify(stats), 200



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


@app.route('/api/status', methods=['GET'])
def status():
    """Affiche le statut du serveur et du système de stockage"""
    with data_lock:
        data_count = len(data_storage)
    
    oldest = None
    newest = None
    if data_storage:
        with data_lock:
            oldest = data_storage[0].timestamp.isoformat()
            newest = data_storage[-1].timestamp.isoformat()
    
    return jsonify({
        'running': is_running,
        'data_count': data_count,
        'oldest_data': oldest,
        'newest_data': newest,
        'retention_minutes': CONFIG['data_retention_minutes'],
        'polling_interval': CONFIG['polling_interval']
    }), 200


@app.route('/', methods=['GET'])
def index():
    """Page web pour visualiser les graphiques"""
    return get_dashboard_html()


def get_dashboard_html():
    """Retourne le HTML de la page de visualisation"""
    return '''
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>TC66C Dashboard</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(90deg,rgba(188, 207, 184, 1) 0%, rgba(189, 194, 180, 1) 10%);
                min-height: 100vh;
                padding: 20px;
            }
            
            .container {
                max-width: 1400px;
                margin: 0 auto;
            }
            
            header {
                background: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                margin-bottom: 30px;
                text-align: center;
            }
            
            h1 {
                color: #333;
                font-size: 2.5em;
                margin-bottom: 10px;
            }
            
            .status-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin-top: 20px;
            }
            
            .status-card {
                background: #f8f9fa;
                padding: 15px;
                border-radius: 8px;
                border-left: 4px solid #40AD40;
            }
            
            .status-card label {
                display: block;
                font-size: 0.9em;
                color: #666;
                margin-bottom: 5px;
                font-weight: 600;
            }
            
            .status-card value {
                display: block;
                font-size: 1.5em;
                color: #333;
                font-weight: bold;
            }
            
            .controls {
                background: white;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                margin-bottom: 30px;
                display: flex;
                gap: 15px;
                align-items: center;
                flex-wrap: wrap;
            }
            
            .controls label {
                font-weight: 600;
                color: #333;
            }
            
            .controls select, .controls button {
                padding: 10px 15px;
                border: 1px solid #ddd;
                border-radius: 5px;
                font-size: 1em;
                cursor: pointer;
                background: white;
            }
            
            .controls button {
                background: #40AD40;
                color: white;
                border: none;
                font-weight: 600;
                transition: background 0.3s;
            }
            
            .controls button:hover {
                background: #5DC95D;
            }
            
            .charts-grid {
                display: grid;
                grid-template-columns: 1fr;
                gap: 30px;
                margin-bottom: 30px;
            }
            
            .chart-container {
                background: white;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }
            
            .chart-container h2 {
                color: #333;
                font-size: 1.3em;
                margin-bottom: 15px;
                padding-bottom: 10px;
                border-bottom: 2px solid #3ee553;
            }
            
            canvas {
                max-height: 300px;
            }
            
            .loading {
                text-align: center;
                color: white;
                font-size: 1.2em;
            }
            
            @media (max-width: 768px) {
                .charts-grid {
                    grid-template-columns: 1fr;
                }
                
                h1 {
                    font-size: 1.8em;
                }
                
                .controls {
                    flex-direction: column;
                    align-items: stretch;
                }
                
                .controls select, .controls button {
                    width: 100%;
                }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <h1> Dashboard</h1>
                <div class="status-grid">
                    <div class="status-card">
                        <label>Données stockées</label>
                        <value id="dataCount">-</value>
                    </div>
                    <div class="status-card">
                        <label>Dernière mise à jour</label>
                        <value id="lastUpdate">-</value>
                    </div>
                    <div class="status-card">
                        <label>Courant actuel</label>
                        <value id="currentCurrent">- A</value>
                    </div>
                    <div class="status-card">
                        <label>Puissance actuelle</label>
                        <value id="currentPower">- W</value>
                    </div>
                </div>
            </header>
            
            <div class="controls">
                <label for="timePeriod">Période:</label>
                <select id="timePeriod">
                    <option value="1m">1 minute</option>
                    <option value="3m">3 minutes</option>
                    <option value="5m">5 minutes</option>
                    <option value="10m">10 minutes</option>
                </select>
                <button onclick="updateCharts()">Actualiser</button>
            </div>
            
            <div class="charts-grid">
                <div class="chart-container">
                    <h2>Courant (A)</h2>
                    <canvas id="currentChart"></canvas>
                </div>
                <div class="chart-container">
                    <h2>Puissance (W)</h2>
                    <canvas id="powerChart"></canvas>
                </div>
            </div>
        </div>
        
        <script>
            let voltageChart, currentChart, powerChart;
            
            const chartConfig = {
                type: 'line',
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    plugins: {
                        legend: {
                            display: false
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: false,
                            ticks: {
                                color: '#666'
                            },
                            grid: {
                                color: '#f0f0f0'
                            }
                        },
                        x: {
                            ticks: {
                                color: '#666'
                            },
                            grid: {
                                color: '#f0f0f0'
                            }
                        }
                    }
                }
            };
            
            function initCharts() {
                currentChart = new Chart(document.getElementById('currentChart'), {
                    ...chartConfig,
                    data: {
                        labels: [],
                        datasets: [{
                            label: 'Courant (A)',
                            data: [],
                            borderColor: '#22C55E',
                            backgroundColor: 'rgba(34, 197, 94, 0.1)',
                            borderWidth: 2,
                            tension: 0.4,
                            fill: true
                        }]
                    }
                });
                
                powerChart = new Chart(document.getElementById('powerChart'), {
                    ...chartConfig,
                    data: {
                        labels: [],
                        datasets: [{
                            label: 'Puissance (W)',
                            data: [],
                            borderColor: '#36A2EB',
                            backgroundColor: 'rgba(54, 162, 235, 0.1)',
                            borderWidth: 2,
                            tension: 0.4,
                            fill: true
                        }]
                    }
                });
            }
            
            async function updateCharts() {
                const period = document.getElementById('timePeriod').value;
                
                try {
                    const response = await fetch(`/api/data/${period}`);
                    const result = await response.json();
                    
                    if (!response.ok) {
                        console.error('Erreur:', result);
                        return;
                    }
                    
                    const data = result.data;
                    
                    if (data.length === 0) {
                        console.log('Pas de données pour cette période');
                        return;
                    }
                    
                    // Extraction des données
                    const labels = data.map(d => {
                        const date = new Date(d.timestamp);
                        return date.toLocaleTimeString('fr-FR');
                    });
                    
                    const currents = data.map(d => d.current);
                    const powers = data.map(d => d.power);
                    
                    // Mise à jour des graphiques
                    currentChart.data.labels = labels;
                    currentChart.data.datasets[0].data = currents;
                    currentChart.update();
                    
                    powerChart.data.labels = labels;
                    powerChart.data.datasets[0].data = powers;
                    powerChart.update();
                    
                } catch (error) {
                    console.error('Erreur lors du chargement des données:', error);
                }
            }
            
            async function updateStatus() {
                try {
                    const response = await fetch('/api/status');
                    const status = await response.json();
                    
                    document.getElementById('dataCount').textContent = status.data_count;
                    
                    if (status.newest_data) {
                        const date = new Date(status.newest_data);
                        document.getElementById('lastUpdate').textContent = date.toLocaleTimeString('fr-FR');
                    }
                    
                    const latestResponse = await fetch('/api/data/latest');
                    if (latestResponse.ok) {
                        const latest = await latestResponse.json();
                        document.getElementById('currentCurrent').textContent = latest.current.toFixed(3) + ' A';
                        document.getElementById('currentPower').textContent = latest.power.toFixed(2) + ' W';
                    }
                } catch (error) {
                    console.error('Erreur lors de la mise à jour du statut:', error);
                }
            }
            
            // Initialisation
            document.addEventListener('DOMContentLoaded', function() {
                initCharts();
                updateStatus();
                updateCharts();
                
                // Mise à jour automatique toutes les 5 secondes
                setInterval(() => {
                    updateStatus();
                    updateCharts();
                }, 5000);
            });
        </script>
    </body>
    </html>
    '''


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
