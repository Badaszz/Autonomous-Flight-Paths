"""Post-hoc analysis of the SITL mission logs. Run from repo root: python analysis/analyze.py"""
import json, math, pathlib
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = pathlib.Path(__file__).resolve().parents[1]
RAW, OUT = ROOT / "data/raw", ROOT / "results"
(OUT / "figures").mkdir(parents=True, exist_ok=True)

HOME_LAT, HOME_LON = -35.363262, 149.165237   # first logged sample of Dataset B
TARGET_ALT, R_EARTH = 20.0, 6378137.0

def to_enu(lat, lon):
    e = np.radians(np.asarray(lon) - HOME_LON) * R_EARTH * math.cos(math.radians(HOME_LAT))
    n = np.radians(np.asarray(lat) - HOME_LAT) * R_EARTH
    return e, n

def wp_grid_B(): return [(0, -10), (0, 10), (10, 10), (10, -10)]
def wp_circle(r=15, n=12):
    return [(r*math.cos(2*math.pi*i/n), r*math.sin(2*math.pi*i/n)) for i in range(n)]
def wp_grid_A():
    return [(i, j if (i//10) % 2 == 0 else 20-j) for i in (0, 10, 20) for j in (0, 10, 20)]

# key: (file, mission filter, waypoints (N,E), dwell s, samples per waypoint, dataset)
RUNS = {
    "B_grid":   ("grid_mission_log.csv",   None,       wp_grid_B(), 5, 5, "B"),
    "B_circle": ("circle_mission_log.csv", None,       wp_circle(), 5, 5, "B"),
    "A_grid":   ("mission_log.csv",        "Grid",     wp_grid_A(), 3, 1, "A"),
    "A_circle": ("mission_log.csv",        "Circular", wp_circle(), 3, 1, "A"),
}
COLS = {"Time (s)": "Time", "Battery (%)": "Battery", "Camera Trigger Count": "Camera_Trigger"}

def seg_dist(p, a, b):
    ab, ap = b - a, p - a
    L2 = float(ab @ ab)
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, float(ap @ ab) / L2))
    return float(np.linalg.norm(p - (a + t*ab)))

def cte(pt, poly):
    return min(seg_dist(pt, poly[k], poly[k+1]) for k in range(len(poly)-1))

def load(key):
    f, m, *_ = RUNS[key]
    d = pd.read_csv(RAW / f).rename(columns=COLS)
    if m: d = d[d.Mission == m].reset_index(drop=True)
    d["E"], d["N"] = to_enu(d.Latitude, d.Longitude)
    return d

def analyse(key):
    d = load(key); _, _, wps, dwell, per, ds = RUNS[key]
    cmd = np.array([(0.0, 0.0)] + [(e, n) for n, e in wps])
    pts = d[["E", "N"]].to_numpy()
    d["CTE"] = [cte(p, cmd) for p in pts]
    d["wp_idx"] = np.minimum(np.arange(len(d)) // per, len(wps)-1)
    act = np.array([[wps[i][1], wps[i][0]] for i in d.wp_idx])
    d["dist_active_wp"] = np.linalg.norm(pts - act, axis=1)
    last = d.groupby("wp_idx").tail(1)
    alt_err = d.Altitude - TARGET_ALT
    dur = float(d.Time.iloc[-1] - d.Time.iloc[0])
    m = dict(run=key, dataset=ds, n_waypoints=len(wps), dwell_s=dwell, n_samples=len(d),
        duration_s=round(dur, 2), nominal_window_s=len(wps)*dwell,
        cte_mean_m=d.CTE.mean(), cte_rms_m=float(np.sqrt((d.CTE**2).mean())),
        cte_max_m=d.CTE.max(), cte_std_m=d.CTE.std(),
        wp_dist_end_of_dwell_mean_m=last.dist_active_wp.mean(),
        wp_dist_end_of_dwell_max_m=last.dist_active_wp.max(),
        alt_rmse_m=float(np.sqrt((alt_err**2).mean())), alt_maxabs_m=alt_err.abs().max(),
        speed_mean_ms=d.Velocity.mean(), speed_max_ms=d.Velocity.max(),
        batt_start=int(d.Battery.iloc[0]), batt_end=int(d.Battery.iloc[-1]),
        batt_rate_pp_per_s=float((d.Battery.iloc[0]-d.Battery.iloc[-1])/dur),
        cam_counter_end=int(d.Camera_Trigger.iloc[-1]))
    return d, cmd, m

def main():
    res, data = [], {}
    for k in RUNS:
        d, cmd, m = analyse(k); res.append(m); data[k] = (d, cmd)
    M = pd.DataFrame(res).set_index("run")
    M.round(3).to_csv(OUT / "metrics.csv")
    (OUT / "metrics.json").write_text(json.dumps(M.round(4).reset_index().to_dict("records"), indent=2))
    print(M.round(2).T.to_string())
    col = {"grid": "tab:blue", "circle": "tab:orange"}
    for ds in ("B", "A"):
        fig, ax = plt.subplots(1, 2, figsize=(10, 4.6))
        for a, s in zip(ax, ("grid", "circle")):
            d, cmd = data[f"{ds}_{s}"]
            a.plot(cmd[:, 0], cmd[:, 1], "k--", lw=1, label="Commanded path")
            a.plot(cmd[1:, 0], cmd[1:, 1], "ks", ms=5, label="Waypoints")
            a.plot(d.E, d.N, "-o", ms=3, color=col[s], label="Flown (logged)")
            a.plot(0, 0, "g^", ms=9, label="Home")
            a.set_aspect("equal"); a.grid(alpha=.3)
            a.set_xlabel("East (m)"); a.set_ylabel("North (m)")
            a.set_title(f"{s.capitalize()} mission (dataset {ds})")
        ax[0].legend(fontsize=8); fig.tight_layout()
        fig.savefig(OUT / f"figures/tracks_{ds}.png", dpi=200); plt.close(fig)
        fig, ax = plt.subplots(1, 2, figsize=(10, 3.6))
        for a, s in zip(ax, ("grid", "circle")):
            d, _ = data[f"{ds}_{s}"]; mm = M.loc[f"{ds}_{s}"]
            a.plot(d.Time, d.CTE, "-o", ms=3, color=col[s])
            a.axhline(mm.cte_rms_m, ls=":", c="k", label=f"RMS = {mm.cte_rms_m:.2f} m")
            a.set_xlabel("Time (s)"); a.set_ylabel("Cross-track error (m)")
            a.set_title(f"{s.capitalize()} (dataset {ds})"); a.grid(alpha=.3); a.legend(fontsize=8)
        fig.tight_layout(); fig.savefig(OUT / f"figures/cte_{ds}.png", dpi=200); plt.close(fig)
    fig, ax = plt.subplots(1, 3, figsize=(13, 3.6))
    for s in ("grid", "circle"):
        d, _ = data[f"B_{s}"]
        for a, y in zip(ax, ("Altitude", "Velocity", "Battery")):
            a.plot(d.Time, d[y], "-o", ms=3, color=col[s], label=s.capitalize())
    ax[0].axhline(TARGET_ALT, c="k", ls=":", lw=1)
    for a, y in zip(ax, ("Altitude (m)", "Speed (m/s)", "SITL battery (%)")):
        a.set_xlabel("Time (s)"); a.set_ylabel(y); a.grid(alpha=.3); a.legend(fontsize=8)
    fig.tight_layout(); fig.savefig(OUT / "figures/alt_speed_batt_B.png", dpi=200); plt.close(fig)

if __name__ == "__main__":
    main()