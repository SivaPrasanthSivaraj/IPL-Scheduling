# Optimization results

## Verified run

The saved run uses all 56 directed 2019 league fixtures, a 56-day horizon, one
match per day, and one full non-playing day between matches for each team.
Independent post-solution validation found zero constraint violations.

| Metric | Historical 2019 | Travel-optimized incumbent |
| --- | ---: | ---: |
| Matches | 56 | 56 |
| Total travel | 98,350.76 km | 89,227.92 km |
| Maximum individual travel | 13,500.79 km | 15,846.49 km |
| Total-travel reduction | — | 9.28% |

CBC stopped at the configured 180-second limit with a feasible integer
incumbent. Therefore this result is **travel-improved but not proven globally
optimal**. The objective directly contains each team's consecutive-match
travel arcs; the improvement is not post-processing.

The increased maximum individual distance demonstrates the efficiency versus
fairness trade-off: minimizing tournament-wide travel does not guarantee that
the worst-travelling team improves. A later fairness objective can minimize
this maximum explicitly.

## Reproduce

```powershell
python inspect_data.py
python build_distances.py
python run_optimization.py
python -m pytest -q
streamlit run app.py
```

Saved schedules, team-level travel totals, and the comparison are in
`outputs/`.
