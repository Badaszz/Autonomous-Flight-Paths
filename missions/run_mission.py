"""python missions/run_mission.py grid|circle --connect 127.0.0.1:5555 [--out file.csv]
Needs DroneKit 2.9.2 in a venv with Python <= 3.9 (see docs/setup.md)."""
import argparse, csv, math, time
from dronekit import connect, VehicleMode, LocationGlobalRelative

ALT, ARRIVE_RADIUS, WP_TIMEOUT, LOG_PERIOD, EARTH_R = 20.0, 1.0, 30.0, 1.0, 6378137.0

def offset(home, north, east, alt=ALT):
    lat = home.lat + math.degrees(north / EARTH_R)
    lon = home.lon + math.degrees(east / (EARTH_R * math.cos(math.radians(home.lat))))
    return LocationGlobalRelative(lat, lon, alt)

def grid_waypoints(length=20.0, spacing=10.0, lines=2):
    wps = []
    for i in range(lines):
        e = [-length/2, length/2] if i % 2 == 0 else [length/2, -length/2]
        wps += [(i*spacing, e[0]), (i*spacing, e[1])]
    return wps

def circle_waypoints(radius=15.0, n=12, closed=True):
    wps = [(radius*math.cos(2*math.pi*k/n), radius*math.sin(2*math.pi*k/n)) for k in range(n)]
    return wps + [wps[0]] if closed else wps

def horiz_dist(vehicle, target):
    a, b = vehicle.location.global_relative_frame, target
    dn = math.radians(b.lat - a.lat) * EARTH_R
    de = math.radians(b.lon - a.lon) * EARTH_R * math.cos(math.radians(a.lat))
    return math.hypot(dn, de)

def takeoff(vehicle, alt):
    while not vehicle.is_armable: time.sleep(1)
    vehicle.mode = VehicleMode("GUIDED"); vehicle.armed = True
    while not vehicle.armed: time.sleep(0.5)
    vehicle.simple_takeoff(alt)
    while vehicle.location.global_relative_frame.alt < 0.95*alt: time.sleep(0.5)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("shape", choices=["grid", "circle"])
    ap.add_argument("--connect", default="127.0.0.1:5555")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    out = a.out or f"{a.shape}_mission_log.csv"
    vehicle = connect(a.connect, wait_ready=True, timeout=120)
    takeoff(vehicle, ALT)
    home = vehicle.location.global_relative_frame
    wps = grid_waypoints() if a.shape == "grid" else circle_waypoints()
    with open(out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Mission","Time","Latitude","Longitude","Altitude","Velocity",
                    "Battery","Camera_Trigger","Battery_Source","Active_WP"])
        t0 = time.time()
        for k, (n, e) in enumerate(wps):
            target = offset(home, n, e); vehicle.simple_goto(target)
            t_wp, next_log = time.time(), 0.0
            while True:
                now = time.time()
                if now >= next_log:
                    p = vehicle.location.global_relative_frame
                    speed = math.sqrt(sum(v*v for v in vehicle.velocity))
                    lvl = vehicle.battery.level if vehicle.battery else None
                    w.writerow([a.shape, round(now-t0,2), round(p.lat,7), round(p.lon,7),
                                round(p.alt,2), round(speed,2), lvl if lvl is not None else "",
                                int((now-t0)/5), "sitl" if lvl is not None else "unavailable", k])
                    next_log = now + LOG_PERIOD
                if horiz_dist(vehicle, target) < ARRIVE_RADIUS or now - t_wp > WP_TIMEOUT: break
                time.sleep(0.1)
    vehicle.mode = VehicleMode("LAND"); vehicle.close(); print("done ->", out)

if __name__ == "__main__":
    main()