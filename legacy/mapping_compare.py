from dronekit import connect, VehicleMode, LocationGlobalRelative, Command
import time
import math
import csv
from datetime import datetime

# ========== CONNECT TO SITL ==========
print("Connecting to vehicle...")
vehicle = connect('127.0.0.1:5555', wait_ready=True, timeout=120)

# ========== PARAMETERS ==========
ALTITUDE = 20
GRID_SIZE = 20   # meters
GRID_SPACING = 10
CIRC_RADIUS = 15  # meters
LOG_FILE = "mission_log.csv"

# ========== HELPER FUNCTIONS ==========
def arm_and_takeoff(aTargetAltitude):
    print("Arming motors...")
    while not vehicle.is_armable:
        print("Waiting for vehicle to initialise...")
        time.sleep(1)

    vehicle.mode = VehicleMode("GUIDED")
    vehicle.armed = True

    while not vehicle.armed:
        print("Waiting for arming...")
        time.sleep(1)

    print("Taking off!")
    vehicle.simple_takeoff(aTargetAltitude)

    while True:
        print(f" Altitude: {vehicle.location.global_relative_frame.alt:.2f}")
        if vehicle.location.global_relative_frame.alt >= aTargetAltitude * 0.95:
            print("Reached target altitude")
            break
        time.sleep(1)

def get_location_offset_meters(original, dNorth, dEast, alt):
    earth_radius = 6378137.0
    newlat = original.lat + (dNorth / earth_radius) * (180 / math.pi)
    newlon = original.lon + (dEast / (earth_radius * math.cos(math.pi * original.lat / 180))) * (180 / math.pi)
    return LocationGlobalRelative(newlat, newlon, alt)

def goto_location(location):
    vehicle.simple_goto(location)
    time.sleep(3)

def log_data(writer, mission_name, start_time):
    pos = vehicle.location.global_relative_frame
    lat, lon, alt = pos.lat, pos.lon, pos.alt
    vel = math.sqrt(vehicle.velocity[0]**2 + vehicle.velocity[1]**2 + vehicle.velocity[2]**2)
    elapsed = time.time() - start_time

    # Try real battery data, else simulate
    if vehicle.battery and vehicle.battery.level is not None:
        battery_level = vehicle.battery.level
    else:
        battery_level = max(0, 100 - elapsed / 4)  # fallback: 25s per 1% drop

    # Simulated camera trigger
    cam_trigger = int(elapsed / 5)

    writer.writerow([
        mission_name,
        round(elapsed, 2),
        round(lat, 6),
        round(lon, 6),
        round(alt, 2),
        round(vel, 2),
        battery_level,
        cam_trigger
    ])

def generate_grid_path(home):
    waypoints = []
    for i in range(0, GRID_SIZE + 1, GRID_SPACING):
        for j in range(0, GRID_SIZE + 1, GRID_SPACING):
            waypoints.append(get_location_offset_meters(home, i, j if (i // GRID_SPACING) % 2 == 0 else GRID_SIZE - j, ALTITUDE))
    return waypoints

def generate_circular_path(home):
    waypoints = []
    for theta in range(0, 360, 30):
        x = CIRC_RADIUS * math.cos(math.radians(theta))
        y = CIRC_RADIUS * math.sin(math.radians(theta))
        waypoints.append(get_location_offset_meters(home, x, y, ALTITUDE))
    return waypoints

# ========== MAIN FLIGHT LOGIC ==========
with open(LOG_FILE, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["Mission", "Time (s)", "Latitude", "Longitude", "Altitude", "Velocity", "Battery (%)", "Camera Trigger Count"])

    home = vehicle.location.global_relative_frame

    # ---- GRID MISSION ----
    print("\n--- Starting GRID mission ---")
    arm_and_takeoff(ALTITUDE)
    start_time = time.time()
    for wp in generate_grid_path(home):
        goto_location(wp)
        log_data(writer, "Grid", start_time)
    vehicle.mode = VehicleMode("RTL")
    time.sleep(10)

    # ---- CIRCULAR MISSION ----
    print("\n--- Starting CIRCULAR mission ---")
    arm_and_takeoff(ALTITUDE)
    start_time = time.time()
    for wp in generate_circular_path(home):
        goto_location(wp)
        log_data(writer, "Circular", start_time)
    vehicle.mode = VehicleMode("RTL")
    time.sleep(10)

print("Missions complete, data saved to", LOG_FILE)
vehicle.close()
