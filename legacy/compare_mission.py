import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# --- Load CSV data ---
grid_file = "grid_mission_log.csv"
circular_file = "circle_mission_log.csv"

grid_df = pd.read_csv(grid_file)
circular_df = pd.read_csv(circular_file)

# --- Ensure battery starts at 100% for both ---
grid_df["Battery"] = grid_df["Battery"]  
circular_df["Battery"] = circular_df["Battery"] 

# --- Compute Velocity if needed ---
if "Velocity" not in grid_df.columns or grid_df["Velocity"].isnull().all():
    grid_df["Velocity"] = np.sqrt(grid_df["Latitude"].diff()**2 + grid_df["Longitude"].diff()**2) / grid_df["Time"].diff()
    circular_df["Velocity"] = np.sqrt(circular_df["Latitude"].diff()**2 + circular_df["Longitude"].diff()**2) / circular_df["Time"].diff()

# --- Plot Battery over Time (Side by Side) ---
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

# Grid Path
ax1.plot(grid_df["Time"], grid_df["Battery"], label="Grid Path", marker='o', color='blue')
ax1.set_xlabel("Time (s)")
ax1.set_ylabel("Battery (%)")
ax1.set_title("Battery Level vs Time - Grid Path")
ax1.grid(True)
ax1.legend()

# Circular Path
ax2.plot(circular_df["Time"], circular_df["Battery"], label="Circular Path", marker='o', color='orange')
ax2.set_xlabel("Time (s)")
ax2.set_ylabel("Battery (%)")
ax2.set_title("Battery Level vs Time - Circular Path")
ax2.grid(True)
ax2.legend()

plt.tight_layout()
plt.show()

# --- Plot Camera Triggers (Side by Side) ---
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

# Grid Path
ax1.step(grid_df["Time"], grid_df["Camera_Trigger"], label="Grid Path", where='post', color='blue')
ax1.set_xlabel("Time (s)")
ax1.set_ylabel("Camera Trigger Count")
ax1.set_title("Camera Triggers vs Time - Grid Path")
ax1.grid(True)
ax1.legend()

# Circular Path
ax2.step(circular_df["Time"], circular_df["Camera_Trigger"], label="Circular Path", where='post', color='orange')
ax2.set_xlabel("Time (s)")
ax2.set_ylabel("Camera Trigger Count")
ax2.set_title("Camera Triggers vs Time - Circular Path")
ax2.grid(True)
ax2.legend()

plt.tight_layout()
plt.show()

# --- Plot Altitude vs Time (Side by Side) ---
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

# Grid Path
ax1.plot(grid_df["Time"], grid_df["Altitude"], label="Grid Path", marker='o', color='blue')
ax1.set_xlabel("Time (s)")
ax1.set_ylabel("Altitude (m)")
ax1.set_title("Altitude Stability - Grid Path")
ax1.grid(True)
ax1.legend()

# Circular Path
ax2.plot(circular_df["Time"], circular_df["Altitude"], label="Circular Path", marker='o', color='orange')
ax2.set_xlabel("Time (s)")
ax2.set_ylabel("Altitude (m)")
ax2.set_title("Altitude Stability - Circular Path")
ax2.grid(True)
ax2.legend()

plt.tight_layout()
plt.show()

# --- Plot Velocity vs Time (Side by Side) ---
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

# Grid Path
ax1.plot(grid_df["Time"], grid_df["Velocity"], label="Grid Path", marker='o', color='blue')
ax1.set_xlabel("Time (s)")
ax1.set_ylabel("Velocity (m/s)")
ax1.set_title("Velocity vs Time - Grid Path")
ax1.grid(True)
ax1.legend()

# Circular Path
ax2.plot(circular_df["Time"], circular_df["Velocity"], label="Circular Path", marker='o', color='orange')
ax2.set_xlabel("Time (s)")
ax2.set_ylabel("Velocity (m/s)")
ax2.set_title("Velocity vs Time - Circular Path")
ax2.grid(True)
ax2.legend()

plt.tight_layout()
plt.show()

# --- Optional: Compute and Plot Path Deviation ---
def haversine(lat1, lon1, lat2, lon2):
    # Haversine distance in meters
    R = 6371000
    phi1, phi2 = np.radians(lat1), np.radians(lat2)
    dphi = np.radians(lat2 - lat1)
    dlambda = np.radians(lon2 - lon1)
    a = np.sin(dphi/2.0)**2 + np.cos(phi1)*np.cos(phi2)*np.sin(dlambda/2.0)**2
    return 2*R*np.arcsin(np.sqrt(a))

grid_df["Deviation"] = [0] + [haversine(grid_df.Latitude.iloc[i-1], grid_df.Longitude.iloc[i-1],
                                         grid_df.Latitude.iloc[i], grid_df.Longitude.iloc[i])
                               for i in range(1, len(grid_df))]
circular_df["Deviation"] = [0] + [haversine(circular_df.Latitude.iloc[i-1], circular_df.Longitude.iloc[i-1],
                                            circular_df.Latitude.iloc[i], circular_df.Longitude.iloc[i])
                                  for i in range(1, len(circular_df))]

plt.figure(figsize=(15,6))
ax1 = plt.subplot(1, 2, 1)
ax1.plot(grid_df["Time"], grid_df["Deviation"], label="Grid Path", marker='o', color='blue')
ax1.set_xlabel("Time (s)")
ax1.set_ylabel("Path Deviation (m)")
ax1.set_title("Path Deviation vs Time - Grid Path")
ax1.grid(True)
ax1.legend()

ax2 = plt.subplot(1, 2, 2)
ax2.plot(circular_df["Time"], circular_df["Deviation"], label="Circular Path", marker='o', color='orange')
ax2.set_xlabel("Time (s)")
ax2.set_ylabel("Path Deviation (m)")
ax2.set_title("Path Deviation vs Time - Circular Path")
ax2.grid(True)
ax2.legend()

plt.tight_layout()
plt.show()
