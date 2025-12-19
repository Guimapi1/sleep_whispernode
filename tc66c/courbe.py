import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import numpy as np

# Charger les données depuis le fichier CSV
file_path = "TC66_20251219113127.csv"
data = pd.read_csv(file_path)

# Définition des zones
zones = [
    (0, 22, "Wattmètre seul", "lightgray"),
    (22, 24, "Connexion whispernode", "yellow"),
    (24, 30, "Deep sleep", "lightgreen"),
    (30, 38, "Whispernode réveillé", "lightblue"),
    (38, 44, "Deep sleep", "lightgreen"),
    (44, 51, "Whispernode réveillé", "lightblue"),
    (51, 57, "Deep sleep", "lightgreen"),
    (57, 65, "Whispernode réveillé", "lightblue"),
    (65, 71, "Deep sleep", "lightgreen"),
    (71, 78, "Whispernode réveillé", "lightblue"),
    (78, 84, "Deep sleep", "lightgreen"),
    (84, 85, "Whispernode réveillé", "lightblue"),
    (85, 88, "Déconnexion whispernode", "orange"),
    (88, 100, "Wattmètre seul", "lightgray"),
]

Zones_legend = zones.copy()

# Phases pour calcul des moyennes
target_labels = ["Wattmètre seul", "Deep sleep"]

phase_means_power = {}
phase_means_current = {}

# Calcul des moyennes pour chaque type de phase
for label in target_labels:
    power_vals = []
    curr_vals = []

    for start, end, zlabel, _ in zones:
        if zlabel == label:
            mask = (data["Time[S]"] >= start) & (data["Time[S]"] <= end)
            p = data.loc[mask, "Power[W]"].mean()
            c = data.loc[mask, "Current[A]"].mean()
            if pd.notna(p):
                power_vals.append(p)
            if pd.notna(c):
                curr_vals.append(c)

    if power_vals:
        phase_means_power[label] = np.mean(power_vals)
    if curr_vals:
        phase_means_current[label] = np.mean(curr_vals)

# ------------ PLOTS -------------

plt.figure(figsize=(12, 10))

# ===================================================================
#                        TRACÉ PUISSANCE
# ===================================================================
ax1 = plt.subplot(2, 1, 1)
ax1.plot(data["Time[S]"], data["Power[W]"], color="blue", label="Puissance (W)")
ax1.set_title("Puissance et Intensité en fonction du temps")
ax1.set_ylabel("Puissance (W)")
ax1.grid(True)

# Coloration des zones
for start, end, label, color in zones:
    ax1.axvspan(start, end, color=color, alpha=0.4)

# Lignes + rectangles pour moyennes de puissance
y_top = data["Power[W]"].max()
y_text = y_top * 0.9  # juste en dessous du max

for i, (label, val) in enumerate(phase_means_power.items()):
    ax1.hlines(val, 0, 100, colors="magenta", linestyles="--", alpha=0.7)
    ax1.text(
        5,                   # position x fixe au début du graphe
        val,                 # position verticale = valeur moyenne
        f"{label}: {val:.5f} W",
        va="center",
        fontsize=9,
        bbox=dict(boxstyle="round,pad=0.2", facecolor="pink", edgecolor="red")
    )

# ===================================================================
#                        TRACÉ INTENSITÉ
# ===================================================================
ax2 = plt.subplot(2, 1, 2)
ax2.plot(data["Time[S]"], data["Current[A]"], color="red", label="Intensité (A)")
ax2.set_xlabel("Temps (s)")
ax2.set_ylabel("Intensité (A)")
ax2.grid(True)

# Coloration
for start, end, label, color in zones:
    ax2.axvspan(start, end, color=color, alpha=0.4)

# Lignes + rectangles pour moyennes d’intensité
for i, (label, val) in enumerate(phase_means_current.items()):
    ax2.hlines(val, 0, 100, colors="magenta", linestyles="--", alpha=0.7)
    ax2.text(
        5,
        val,
        f"{label}: {val:.6f} A",
        va="center",
        fontsize=9,
        bbox=dict(boxstyle="round,pad=0.2", facecolor="pink", edgecolor="red")
    )

# ---------------------- LÉGENDE PROPRE --------------------------

zone_labels = {}
for _, _, label, color in zones:
    if label not in zone_labels:
        zone_labels[label] = Patch(facecolor=color, edgecolor="black", alpha=0.4, label=label)



mean_patch = Patch(facecolor="pink", edgecolor="red", label="Moyenne (Puissance & Intensité)")

ax1.legend(
    handles=[plt.Line2D([], [], color="blue", label="Puissance (W)"),
             mean_patch] +
            list(zone_labels.values()),
    loc="upper right"
)

ax2.legend(
    handles=[plt.Line2D([], [], color="red", label="Intensité (A)"),
             mean_patch] +
            list(zone_labels.values()),
    loc="upper right"
)

plt.tight_layout()
plt.show()
