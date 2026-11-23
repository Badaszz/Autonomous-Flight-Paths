# AutonomousFlight-Paths

ArduPilot SITL + Gazebo Harmonic + DroneKit-Python: grid and circular waypoint missions, with
logs and post-hoc analysis. Accompanies the JED manuscript (see CITATION.cff).

## Layout
| Path | Contents |
|---|---|
| `data/raw/` | Unmodified logs. `grid_mission_log.csv`, `circle_mission_log.csv` (Dataset B, 1 Hz); `mission_log.csv` (Dataset A, one sample per waypoint) |
| `legacy/` | Scripts exactly as run to produce the raw logs |
| `missions/run_mission.py` | Refactored mission runner with arrival-based waypoints (not used for the paper's data) |
| `analysis/analyze.py` | Recomputes every table and figure from `data/raw/` |
| `results/` | `metrics.csv/json`, `figures/` |
| `docs/setup.md` | Installation and launch commands |

## Reproduce the results
    pip install numpy pandas matplotlib
    python analysis/analyze.py

## Which file made which result
| Paper item | Script | Data |
|---|---|---|
| Table 3, Table 4 | `analysis/analyze.py` | all three CSVs |
| Fig. 3, 4, 5 | `analysis/analyze.py` | Dataset B |
| Fig. 6, 7 | `analysis/analyze.py` | Dataset A |

## Data notes
- Battery is the SITL-simulated level (`vehicle.battery.level`). Camera_Trigger is `int(elapsed/5)`, a timer.
- Dataset A and B used different scripts, dwell times (3 s vs 5 s) and sampling; they are not repeats.
- Pre-arm checks were disabled in the original runs.
- Pin versions in `docs/setup.md` before tagging a release (Zenodo DOI, licence, CITATION.cff still to add).
