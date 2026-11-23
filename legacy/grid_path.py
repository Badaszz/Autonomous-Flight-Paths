from dronekit import connect, VehicleMode, LocationGlobalRelative
import time, math, csv

# --- Connect to vehicle ---
vehicle = connect('127.0.0.1:5555', wait_ready=True)
print("Connected to vehicle")

# --- Logging setup ---
log_file = open("grid_mission_log.csv", "w", newline="")
writer = csv.writer(log_file)
writer.writerow(["Mission", "Time", "Latitude", "Longitude", "Altitude", "Velocity", "Battery", "Camera_Trigger"])

# --- Logging function ---
def log_data(writer, mission_name, start_time):
    pos = vehicle.location.global_relative_frame
    lat, lon, alt = pos.lat, pos.lon, pos.alt
    vel = math.sqrt(sum(v**2 for v in vehicle.velocity))
    elapsed = time.time() - start_time
    battery_level = vehicle.battery.level if vehicle.battery and vehicle.battery.level is not None else max(0, 100 - elapsed / 4)
    cam_trigger = int(elapsed / 5)
    writer.writerow([
        mission_name,
        round(elapsed,2),
        round(lat,6),
        round(lon,6),
        round(alt,2),
        round(vel,2),
        battery_level,
        cam_trigger
    ])
    return lat, lon, alt  # for deviation calculations

# --- Takeoff function ---
def arm_and_takeoff(target_alt):
    vehicle.mode = VehicleMode("GUIDED")
    vehicle.armed = True
    while not vehicle.armed:
        time.sleep(0.5)
    print("Taking off")
    vehicle.simple_takeoff(target_alt)
    while True:
        if vehicle.location.global_relative_frame.alt >= target_alt * 0.95:
            break
        time.sleep(0.5)

# --- Grid path generator ---
def generate_grid_path(center_lat, center_lon, side=20, step=10):
    dLat = step / 111111
    dLon = step / (111111 * math.cos(math.radians(center_lat)))
    points = []
    for i in range(0, side, step):
        lat = center_lat + i / 111111
        lon_offset = [center_lon - dLon, center_lon + dLon] if (i//step) %2==0 else [center_lon + dLon, center_lon - dLon]
        for lon in lon_offset:
            points.append(LocationGlobalRelative(lat, lon, 20))
    return points

# --- Fly path ---
def fly_path(path):
    start_time = time.time()
    positions = []
    for wp in path:
        vehicle.simple_goto(wp)
        # log every second for 5 seconds at this waypoint
        for _ in range(5):
            lat, lon, alt = log_data(writer, "Grid", start_time)
            positions.append((lat, lon, alt))
            time.sleep(1)
    mission_time = time.time() - start_time
    avg_alt = sum(p[2] for p in positions) / len(positions)
    avg_vel = sum(math.sqrt(sum((vehicle.velocity[i])**2 for i in range(3))) for _ in positions)/len(positions)
    print(f"Grid mission finished: time={mission_time:.1f}s, avg_alt={avg_alt:.2f}m, avg_vel={avg_vel:.2f} m/s")
    return positions

# --- Main ---
arm_and_takeoff(20)
home = vehicle.location.global_relative_frame
path = generate_grid_path(home.lat, home.lon)
positions = fly_path(path)
vehicle.mode = VehicleMode("LAND")
log_file.close()
vehicle.close()
print("Grid mission completed, log saved.")
