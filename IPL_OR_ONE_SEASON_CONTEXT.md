# IPL Tournament Scheduling Optimization --- Codex Context

## 1. Project Decision

This project will start **directly with real IPL historical data**.

Do **not** create a separate synthetic 4-team dataset as the main
development path.

However, do **not** optimize all IPL seasons together.

The project will:

-   use the complete historical IPL match dataset for statistics and
    exploration;
-   select **one IPL season** for the initial optimization experiment;
-   build and validate the Integer Programming model on that selected
    season;
-   later allow other seasons to be selected if the implementation is
    stable.

------------------------------------------------------------------------

## 2. Project Title

**Optimization of IPL Tournament Scheduling Using Integer Programming: A
Travel-Efficient and Constraint-Aware Approach**

Short title:

**IPL Tournament Scheduling Optimization**

This is primarily an **Operational Research project**, not a Machine
Learning project.

The main technique is:

**Integer Programming / Binary Integer Programming / MILP**

Python will be used to implement the optimization model and application.

------------------------------------------------------------------------

## 3. Core Problem

Given the teams, fixtures, venues and tournament structure of one IPL
season, generate an IPL-style tournament schedule that satisfies
operational constraints.

After a feasible schedule is working, optimize the schedule to reduce
team travel.

The central question is:

> Given a set of IPL teams, required matches, home venues, scheduling
> slots and operational constraints, what feasible schedule minimizes
> total team travel?

------------------------------------------------------------------------

## 4. Scope

### Historical dataset

Use the complete historical IPL match-level dataset, approximately
covering 2008--2025, for:

-   dataset statistics;
-   season exploration;
-   team analysis;
-   venue analysis;
-   historical scheduling analysis;
-   selecting the season used for optimization;
-   constructing a historical baseline.

### Optimization

For the first working optimization model:

**Use only one selected IPL season.**

Do not combine matches from different seasons into one optimization
problem.

The exact season should be selected **after inspecting the actual
dataset**.

Do not assume a particular season before checking:

-   available seasons;
-   number of teams;
-   number of matches;
-   venue consistency;
-   home venue mappings;
-   unusual tournament formats;
-   neutral venues;
-   missing values.

Prefer a season with a reasonably standard structure for the first
implementation.

------------------------------------------------------------------------

## 5. Dataset

The planning document refers to a Kaggle match-level dataset
approximately named:

**IPL All Matches 2008--2025**

The exact dataset file and schema must be inspected before coding
assumptions are made.

Potential columns mentioned in the project planning document include:

-   Season
-   Match date
-   Team 1
-   Team 2
-   Venue
-   City
-   Match type
-   Match number
-   Winner
-   Toss information

### Important

Do not use ball-by-ball data for the core scheduling optimization.

Match-level data is sufficient.

Do not invent column names in code.

First load the actual CSV and inspect:

``` python
df.shape
df.columns
df.head()
df.info()
df.isna().sum()
```

Then inspect important unique values such as:

``` python
df["season"].unique()
df["team1"].unique()
df["team2"].unique()
df["venue"].unique()
```

using the actual column names found in the dataset.

------------------------------------------------------------------------

## 6. First Development Step

The first coding task is **dataset inspection and preprocessing**, not
optimization.

After obtaining the IPL dataset:

1.  load it using Pandas;
2.  inspect its dimensions;
3.  inspect columns;
4.  identify available seasons;
5.  count matches per season;
6.  identify teams per season;
7.  inspect venue names;
8.  inspect city names;
9.  inspect match types;
10. inspect missing values;
11. identify franchise/team-name changes;
12. identify venue-name inconsistencies.

Only after this analysis should the initial optimization season be
selected.

------------------------------------------------------------------------

## 7. Selecting the Initial Season

Create a summary similar to:

  Season       Teams   Matches   Venues Notes
  ---------- ------- --------- -------- -------
  Season A       ...       ...      ... ...
  Season B       ...       ...      ... ...

Then choose one season suitable for the first OR model.

Selection criteria:

-   normal/understandable tournament format;
-   manageable number of teams;
-   complete match information;
-   consistent venues;
-   identifiable home venues;
-   fewer exceptional/neutral-location complications.

Do not select the season merely because it is the newest.

Document why the selected season was chosen.

------------------------------------------------------------------------

## 8. Preprocessing

Create a preprocessing pipeline rather than manually editing the
original CSV.

The cleaned optimization table should approximately contain:

``` text
Season
Date
Team1
Team2
Venue
City
MatchType
```

depending on the actual available columns.

Tasks:

### Team normalization

Historical IPL data may contain renamed/replaced franchises.

Create an explicit mapping only when necessary.

Do not silently merge teams.

### Venue normalization

The same stadium may appear under slightly different historical names.

Create an explicit venue normalization mapping.

### Date normalization

Convert dates to Pandas datetime.

### Season filtering

Create a reusable function such as:

``` python
get_season_data(df, season)
```

### Match filtering

Determine whether playoffs/finals should be included in the
optimization.

For the first scheduling model, it may be easier to optimize
league-stage fixtures only.

This decision must be documented rather than silently applied.

------------------------------------------------------------------------

## 9. Historical Schedule as Baseline

The selected season's historical schedule should be preserved.

It will later be compared against the optimized schedule.

Historical information should include at least:

``` text
Date
Team1
Team2
Venue
```

From this, calculate historical metrics such as:

-   travel per team;
-   total travel;
-   maximum individual team travel;
-   rest gaps;
-   venue usage;
-   home/away distribution where definable.

The historical schedule is the **baseline**.

The optimization model generates the **proposed schedule**.

------------------------------------------------------------------------

## 10. Distance Dataset

A second dataset is required containing distances between relevant IPL
venues.

Suggested long-form structure:

``` csv
from_venue,to_venue,distance_km
Venue A,Venue B,123
Venue A,Venue C,456
...
```

The actual distances must be obtained using a consistent methodology.

Prefer stadium-to-stadium distance where practical.

Do not use arbitrary example distances in final analysis.

Before optimization, validate:

``` text
Every venue used by the selected season
must be represented in the distance data.
```

Create explicit validation code for this.

------------------------------------------------------------------------

## 11. Home Venue Mapping

For the selected season, create a mapping such as:

``` python
home_venues = {
    "Team A": "Venue A",
    "Team B": "Venue B",
}
```

Do not hard-code a generic historical mapping before inspecting the
selected season.

IPL teams may use multiple home venues or neutral venues in some
seasons.

If the selected season contains such complications, document the
simplification used by the academic model.

------------------------------------------------------------------------

## 12. OR Model --- Phase 1: Feasible Schedule

The first optimization milestone is:

> Generate a valid schedule satisfying all required constraints.

Do not begin with travel minimization until feasibility works.

### Conceptual Decision Variable

A binary variable may represent whether fixture `m` is assigned to
scheduling slot `t`:

``` text
x[m,t] = 1 if match m is played in slot t
         0 otherwise
```

Alternatively, a team-pair formulation may be used.

If the home team uniquely determines the venue, avoid unnecessarily
adding a venue dimension to the decision variable.

Choose the simplest mathematically correct formulation.

------------------------------------------------------------------------

## 13. Core Constraints

### Every required fixture is scheduled

Each required fixture from the selected tournament structure must appear
exactly once, unless the chosen format explicitly requires otherwise.

### Team cannot be double-booked

A team cannot participate in two matches in the same scheduling slot.

### Venue cannot be double-booked

A venue cannot host two matches simultaneously.

### Minimum rest

Allow a configurable minimum rest requirement.

Example:

``` text
minimum_rest_days = 1
```

Clearly define what the parameter means.

For example:

> One minimum rest day means there must be at least one full non-playing
> day between two matches for the same team.

### Home venue

When using a home/away model, home fixtures must use the corresponding
team's designated home venue.

------------------------------------------------------------------------

## 14. OR Model --- Phase 2: Travel Minimization

After the feasible scheduling model works, add the primary optimization
objective:

``` text
Minimize total team travel
```

For each team, order its matches chronologically.

If a team plays consecutive matches at:

``` text
Venue A -> Venue B -> Venue C
```

its travel contribution is:

``` text
distance(A, B) + distance(B, C)
```

Total tournament travel is:

``` text
sum(travel of every team)
```

### Critical Modeling Requirement

Travel depends on **consecutive scheduled matches**.

Therefore the solver formulation must correctly represent the
relationship between scheduling decisions and consecutive venue
transitions.

Do not:

1.  generate an arbitrary feasible schedule;
2.  calculate travel afterward;
3.  call it travel optimization.

The travel objective must actually affect the solver's scheduling
decisions.

------------------------------------------------------------------------

## 15. Optional Phase 3: Fairness

Only after total-travel optimization works.

Alternative objective:

``` text
Minimize maximum individual team travel
```

This allows comparison between:

### Efficiency

``` text
Minimize total tournament travel
```

and:

### Fairness

``` text
Minimize the worst travel burden experienced by any team
```

This is optional.

------------------------------------------------------------------------

## 16. Historical vs Optimized Comparison

The final analysis should compare the selected historical season against
the optimized schedule.

Example output structure:

  Metric                    Historical    Optimized
  ----------------------- ------------ ------------
  Matches                   calculated   calculated
  Total travel              calculated   calculated
  Maximum team travel       calculated   calculated
  Minimum rest              calculated   calculated
  Venue usage               calculated   calculated
  Constraint violations        derived            0

Travel reduction can be calculated as:

``` text
((historical_travel - optimized_travel)
 / historical_travel) * 100
```

Only compare values calculated under the same distance and travel
assumptions.

Never hard-code illustrative results.

------------------------------------------------------------------------

## 17. Statistics Module

The complete historical dataset should support a statistics dashboard.

Possible statistics:

### Season

-   matches per season;
-   teams per season;
-   venues per season.

### Team

-   matches played;
-   wins/losses;
-   home/away counts where definable.

### Venue

-   matches hosted;
-   matches by season;
-   venue utilization.

### City

-   matches by city;
-   most-used cities.

### Scheduling

-   average gap between matches;
-   minimum/maximum rest gaps;
-   matches per month;
-   team scheduling patterns.

Statistics are a supporting data-analysis component.

They are not the main OR contribution.

------------------------------------------------------------------------

## 18. Technology Stack

Recommended:

``` text
Python
Pandas
NumPy
PuLP or OR-Tools
Plotly or Matplotlib
Streamlit
```

### Optimization Solver

Use either:

-   PuLP + CBC, or
-   Google OR-Tools.

Choose based on implementation clarity and model requirements.

The mathematical formulation is more important than the specific solver.

### Machine Learning

Machine Learning is **not part of the current project scope**.

Do not add ML unless explicitly requested later.

------------------------------------------------------------------------

## 19. Project Structure

Recommended structure:

``` text
IPL_Optimization/
|
|-- app.py
|
|-- data/
|   |-- ipl_matches.csv
|   `-- venue_distances.csv
|
|-- preprocessing.py
|-- statistics.py
|-- optimizer.py
|-- travel.py
|-- requirements.txt
|-- README.md
`-- PROJECT_CONTEXT.md
```

### `preprocessing.py`

Handles:

-   loading data;
-   cleaning team names;
-   cleaning venue names;
-   date conversion;
-   season filtering;
-   fixture extraction;
-   home venue mappings.

### `statistics.py`

Handles historical descriptive statistics.

### `optimizer.py`

Contains:

-   sets and parameters;
-   decision variables;
-   objective function;
-   constraints;
-   solver execution;
-   solution extraction;
-   schedule validation.

Keep this independent of Streamlit.

### `travel.py`

Handles:

-   distance data;
-   distance lookup;
-   chronological team paths;
-   travel per team;
-   total travel;
-   maximum travel;
-   historical/optimized comparison.

### `app.py`

Streamlit UI only.

It should call functions from the other modules rather than containing
the OR model itself.

------------------------------------------------------------------------

## 20. Validation

After every solver run, independently validate the resulting schedule.

Check:

1.  every required fixture exists exactly as required;
2.  no team is double-booked;
3.  no venue is double-booked;
4.  home venue restrictions are satisfied;
5.  rest constraints are satisfied;
6.  every venue exists in the distance matrix;
7.  all travel paths are ordered chronologically;
8.  solver status is feasible/optimal;
9.  no unexpected duplicate matches exist.

Do not trust solver output without post-solution validation.

------------------------------------------------------------------------

## 21. Development Order

Follow this order.

### Phase 1 --- Dataset

``` text
Obtain IPL dataset
      ->
Inspect dataset
      ->
Clean dataset
      ->
Analyze seasons
      ->
Choose one season
```

### Phase 2 --- Season Model

``` text
Selected season
      ->
Extract teams
      ->
Extract fixtures
      ->
Determine home venues
      ->
Determine available scheduling horizon
```

### Phase 3 --- Feasible OR Model

``` text
Decision variables
      ->
Constraints
      ->
Solver
      ->
Feasible schedule
      ->
Validation
```

### Phase 4 --- Distance Data

``` text
Identify selected-season venues
      ->
Build verified distance matrix
      ->
Validate completeness
```

### Phase 5 --- Travel Optimization

``` text
Feasible model
      +
Distance matrix
      ->
Travel objective
      ->
Minimum-travel schedule
      ->
Validation
```

### Phase 6 --- Comparison

``` text
Historical schedule
vs
Optimized schedule
```

### Phase 7 --- Statistics

Build historical statistics and charts.

### Phase 8 --- UI

Build Streamlit interface.

------------------------------------------------------------------------

## 22. Important Instructions for Codex

1.  Do not create a fake 4-team dataset unless explicitly requested for
    debugging.
2.  Start from the real IPL match dataset.
3.  Use only **one real season** for the initial optimization.
4.  Do not optimize all historical seasons simultaneously.
5.  Inspect the actual dataset before assuming column names.
6.  Do not invent missing data.
7.  Do not invent venue distances.
8.  Do not add ML.
9.  Keep OR logic separate from UI logic.
10. Build feasibility before travel optimization.
11. Validate every generated schedule.
12. If the model is infeasible, report the reason/diagnostics rather
    than silently weakening constraints.
13. Keep the mathematical formulation explainable for an Operational
    Research academic presentation.
14. Prefer incremental implementation over generating the entire
    application at once.
15. Do not claim the model reproduces official IPL scheduling.
16. Document every major simplification.

------------------------------------------------------------------------

## 23. Immediate Next Task

The immediate next task is:

> **Obtain and inspect the real IPL match-level dataset.**

Once the dataset exists in the repository, Codex should create the
preprocessing/inspection code first.

Expected initial output:

``` text
Dataset shape
Column names
Available seasons
Matches per season
Teams per season
Venues per season
Missing-value summary
Potential team-name inconsistencies
Potential venue-name inconsistencies
```

Then recommend a suitable season for the initial optimization based on
the actual data.

Do **not** write the Integer Programming model before this inspection is
complete.

------------------------------------------------------------------------

## 24. Current Status

At the time this file was generated:

-   project topic is finalized;
-   Python is the chosen implementation language;
-   Integer Programming is the core OR technique;
-   one real IPL season will be used for initial optimization;
-   the complete historical dataset will be used for statistics;
-   the exact optimization season has not yet been selected;
-   the IPL dataset itself still needs to be obtained/verified;
-   the venue-distance dataset still needs to be created;
-   the solver library has not yet been permanently fixed;
-   Machine Learning is not currently required;
-   implementation should begin with real-data inspection and
    preprocessing.
