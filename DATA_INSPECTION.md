# Dataset inspection — phase 1

Inspection date: 2026-08-16  
Source file: `ipl.csv`

## Dataset profile

- Shape: 1,169 rows × 19 columns
- Coverage: 18 encoded seasons, corresponding to 2008–2025
- Team labels: 19
- Venue labels: 59 before conservative normalization
- Match types: League, Semi Final, 3rd Place Play-Off, Elimination Final,
  Eliminator, Qualifier 1, Qualifier 2, and Final
- Required scheduling fields (`team1`, `team2`, `match_date`, `venue`, `season`,
  `match_type`) are complete.
- Missing data occurs in `winner` (23), `result_margin` (23), `target_runs`
  (6), `target_overs` (6), and `city` (51). These fields are not required to
  extract fixtures. The missing-city records remain visible in the audit.

The complete per-season results are generated in `outputs/season_summary.csv`.

## Naming findings

Potential franchise changes are present and must not be treated as spelling
errors: Delhi Daredevils → Delhi Capitals, Kings XI Punjab → Punjab Kings,
Royal Challengers Bangalore → Royal Challengers Bengaluru, and Rising Pune
Supergiants → Rising Pune Supergiant. Historical identities such as Deccan
Chargers, Gujarat Lions, Kochi Tuskers Kerala, Pune Warriors, and Rising Pune
Supergiant(s) also appear. Phase 1 preserves all source team labels.

Venue variants include `M Chinnaswamy Stadium` / `M.Chinnaswamy Stadium` and
`Brabourne Stadium` / `Brabourne Stadium, Mumbai`; these two unambiguous pairs
are normalized explicitly. Other venue labels containing cities are retained
until stadium identity is verified rather than guessed. Examples requiring
later review include venue names with changing sponsorship or expanded
location suffixes and the Abu Dhabi labels `Sheikh Zayed Stadium` / `Zayed
Cricket Stadium, Abu Dhabi`.

## Initial optimization season

Season ID **12 (2019)** is selected:

| Property | Value |
| --- | ---: |
| Teams | 8 |
| All matches | 60 |
| League matches | 56 |
| Playoff matches | 4 |
| Venues | 9 |
| Cities | 9 |
| Missing required fields | 0 |

It provides a conventional double round-robin-sized league stage, a manageable
team count, complete scheduling fields, and identifiable Indian home grounds.
It is preferable for the first model to the overseas/neutral or split seasons
and to recent ten-team grouped formats.

The first model will use league matches only. Playoff participants are outcomes
of league standings and are not known fixtures when the league schedule is
created. Historical playoff rows remain in the source data and statistics.

## Boundaries before optimization

No solver model, home-venue mapping, or distance values have yet been created.
The next milestone must verify 2019 home-ground assumptions (including whether
multiple grounds are allowed), define calendar slots and the exact rest rule,
and formulate a feasibility-only binary integer program. Stadium-to-stadium
distances require a consistently sourced dataset before travel minimization.

## Coordinate methodology update

The eight selected-season stadium coordinates are now recorded in
`data/venue_coordinates.csv`, primarily from OpenStreetMap-linked records.
`build_distances.py` applies the haversine formula with mean Earth radius
6,371.0088 km and produces all 64 ordered pairs. These are direct geographic
distances, not road distances or inferred flight itineraries.
