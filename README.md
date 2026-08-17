# IPL Tournament Scheduling Optimization

An Operational Research project that uses binary integer programming to build
an IPL-style tournament schedule and reduce team travel while satisfying
fixture, venue, capacity, and rest constraints.

The complete historical match dataset is used for exploration and statistics.
The initial optimization experiment uses the **2019 IPL league stage** (season
ID `12` in the supplied dataset): 8 teams, 56 directed home/away fixtures, and
8 designated home stadiums. Playoffs are excluded because their participants
depend on league results and are not known when the league schedule is built.

## Verified result

| Metric | Historical 2019 | Optimized incumbent |
| --- | ---: | ---: |
| League matches | 56 | 56 |
| Total travel | 98,350.76 km | 89,227.92 km |
| Maximum individual travel | 13,500.79 km | 15,846.49 km |
| Total-travel reduction | — | 9.28% |
| Constraint violations | Baseline not constrained | 0 |

CBC stopped at the configured 180-second limit with a valid integer incumbent.
The result is therefore travel-improved but **not proven globally optimal**.
The increase in maximum individual travel demonstrates the efficiency versus
fairness trade-off. See [RESULTS.md](RESULTS.md) for interpretation.

## Features

- Inspection of 1,169 historical matches covering 2008–2025
- Reusable preprocessing without editing the source CSV
- Season, team, venue, city, and missing-value reports
- Explicit 2019 double round-robin fixture construction
- Sourced stadium coordinates and reproducible great-circle distances
- Feasibility and total-travel MILP modes using PuLP and CBC
- Consecutive-match travel represented inside the solver objective
- Independent post-solution constraint validation
- Historical versus optimized travel comparison
- Streamlit dashboard and downloadable schedule
- Automated tests for preprocessing, fixtures, distances, and baseline logic

## Project structure

```text
.
|-- app.py                         Streamlit interface
|-- preprocessing.py               Loading, validation, and normalization
|-- statistics.py                  Historical descriptive statistics
|-- fixtures.py                    2019 home venues and fixture construction
|-- travel.py                      Distance and travel calculations
|-- optimizer.py                   MILP formulation and validation
|-- inspect_data.py                Reproducible dataset inspection
|-- build_distances.py             Distance-matrix generator
|-- run_optimization.py            End-to-end solver and comparison runner
|-- ipl.csv                        Historical match-level dataset
|-- data/
|   |-- venue_coordinates.csv      Coordinates with source URLs
|   `-- venue_distances.csv        Generated 8 x 8 distance matrix
|-- outputs/                       Inspection and verified solver outputs
|-- tests/                         Pytest test suite
|-- DATA_INSPECTION.md             Dataset-selection audit
|-- RESULTS.md                     Verified results and limitations
|-- IPL_OR_ONE_SEASON_CONTEXT.md   Original project requirements
`-- requirements.txt
```

## Installation

Python 3.10 or newer is recommended.

### Windows PowerShell

```powershell
git clone https://github.com/SivaPrasanthSivaraj/IPL-Scheduling.git
cd IPL-Scheduling
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### macOS/Linux

```bash
git clone https://github.com/SivaPrasanthSivaraj/IPL-Scheduling.git
cd IPL-Scheduling
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Run the project

Run the dashboard:

```powershell
streamlit run app.py
```

Streamlit prints a local URL, normally `http://localhost:8501`.

Reproduce the full command-line workflow:

```powershell
python inspect_data.py
python build_distances.py
python run_optimization.py
python -m pytest -q
```

`run_optimization.py` can take approximately three minutes because the travel
MILP uses a 180-second CBC limit. It writes schedules and comparisons to
`outputs/`.

## Optimization formulation

### Assignment variables

`x[m,d] = 1` when fixture `m` is assigned to day `d`.

### Travel-transition variables

`z[t,m,n] = 1` when match `n` is team `t`'s next chronological match after
match `m`. These variables ensure stadium-to-stadium travel is part of the MILP
objective rather than a metric calculated only after scheduling.

### Enforced constraints

- Every required directed fixture is scheduled exactly once.
- At most one tournament match is scheduled per day in the initial model.
- A team cannot play twice on the same day.
- A venue cannot host two matches on the same day.
- One full rest day is required between a team's matches by default.
- Every home fixture is fixed to its designated 2019 home stadium.
- Predecessor arcs must agree with chronological match order.

Every extracted schedule is independently checked by `validate_schedule()`.
An invalid or fractional solver result is rejected.

## Distance methodology

The IPL CSV does not contain distances. Coordinates for the eight selected
stadiums are stored with source URLs in `data/venue_coordinates.csv`.
`build_distances.py` applies the haversine formula using a mean Earth radius of
6,371.0088 km and generates all 64 ordered venue pairs.

These values are straight-line stadium-to-stadium great-circle distances. They
are not road distances, airfare distances, or inferred flight routes. Both the
historical and optimized schedules use the same matrix and assumptions.

## Important assumptions and limitations

- This is an IPL-inspired academic model, not a reproduction of the BCCI's
  official scheduling process.
- Only the 2019 league stage is optimized.
- The horizon contains 56 days with at most one match per day.
- Broadcast slots, stadium availability, weather, security, workload, and
  commercial preferences are outside the current scope.
- Travel before a team's first match and after its final match is excluded.
- Franchise name changes are not silently merged across historical seasons.
- The saved optimized schedule is a time-limited feasible incumbent.

## Key generated files

- `outputs/historical_2019_league.csv`
- `outputs/feasible_schedule.csv`
- `outputs/optimized_schedule.csv`
- `outputs/historical_travel_by_team.csv`
- `outputs/optimized_travel_by_team.csv`
- `outputs/historical_vs_optimized.csv`
- `outputs/season_summary.csv`

## Tests

```powershell
python -m pytest -q
```

The expected result for the current repository is `7 passed`.
