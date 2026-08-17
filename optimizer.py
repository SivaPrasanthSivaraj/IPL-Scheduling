"""Explainable time-indexed MILP for feasible and minimum-travel schedules."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from itertools import permutations
from time import perf_counter

import pandas as pd
import pulp

from travel import distance_lookup


@dataclass
class OptimizationResult:
    status: str
    schedule: pd.DataFrame
    objective_km: float | None
    solve_seconds: float
    message: str


def _warm_start_order(fixtures: pd.DataFrame) -> list[int] | None:
    """Construct two round-robin legs with no team on adjacent match days."""
    teams = sorted(set(fixtures.home_team) | set(fixtures.away_team))
    if len(teams) % 2: return None
    rotating = teams[:]
    pair_rounds = []
    for _ in range(len(teams) - 1):
        pair_rounds.append([(rotating[i], rotating[-1 - i]) for i in range(len(teams) // 2)])
        rotating = [rotating[0], rotating[-1], *rotating[1:-1]]
    index = {(r.home_team, r.away_team): i for i, r in fixtures.iterrows()}
    rounds = []
    for pairs in pair_rounds:
        rounds.append([index[(min(a, b), max(a, b))] for a, b in pairs])
    for pairs in pair_rounds:
        rounds.append([index[(max(a, b), min(a, b))] for a, b in pairs])
    participants = {i: {r.home_team, r.away_team} for i, r in fixtures.iterrows()}

    def arrange(round_number: int, previous: int | None, result: list[int]) -> list[int] | None:
        if round_number == len(rounds): return result
        for ordered in permutations(rounds[round_number]):
            if previous is None or participants[previous].isdisjoint(participants[ordered[0]]):
                found = arrange(round_number + 1, ordered[-1], result + list(ordered))
                if found is not None: return found
        return None
    return arrange(0, None, [])


def _dates(start_date: pd.Timestamp, horizon_days: int) -> list[pd.Timestamp]:
    return [start_date + timedelta(days=i) for i in range(horizon_days)]


def optimize_schedule(fixtures: pd.DataFrame, distances: pd.DataFrame,
                      *, start_date: str | pd.Timestamp = "2019-03-23",
                      horizon_days: int = 56, minimum_rest_days: int = 1,
                      max_matches_per_day: int = 1, minimize_travel: bool = True,
                      time_limit_seconds: float = 120.0) -> OptimizationResult:
    """Solve the schedule. One rest day means match dates differ by at least two."""
    if minimum_rest_days < 0 or horizon_days < 1 or max_matches_per_day < 1:
        raise ValueError("Invalid scheduling parameter")
    f = fixtures.reset_index(drop=True)
    dates = _dates(pd.Timestamp(start_date), horizon_days)
    teams = sorted(set(f.home_team) | set(f.away_team))
    venues = sorted(f.venue.unique())
    games = {team: [i for i, r in f.iterrows() if team in (r.home_team, r.away_team)] for team in teams}

    # x[i,d] assigns fixture i to date d. z[t,i,j] makes j the next match after i.
    x_index, z_index, n = {}, {}, 0
    for i in range(len(f)):
        for d in range(horizon_days): x_index[i, d], n = n, n + 1
    if minimize_travel:
        for team in teams:
            nodes = games[team]
            for i in [-1] + nodes:  # -1 is source
                for j in nodes + [-2]:  # -2 is sink
                    if i != j and i != -2 and j != -1 and not (i == -1 and j == -2):
                        z_index[team, i, j], n = n, n + 1

    c = [0.0] * n
    if minimize_travel:
        lookup = distance_lookup(distances)
        for (team, i, j), idx in z_index.items():
            if i >= 0 and j >= 0:
                c[idx] = lookup[(f.iloc[i].venue, f.iloc[j].venue)]

    rows: list[tuple[dict[int, float], float | None, float | None]] = []
    def add(coefs, lower=None, upper=None): rows.append((coefs, lower, upper))

    # Every fixture exactly once.
    for i in range(len(f)):
        add({x_index[i, d]: 1 for d in range(horizon_days)}, 1, 1)
    # Tournament and venue daily capacities.
    for d in range(horizon_days):
        add({x_index[i, d]: 1 for i in range(len(f))}, upper=max_matches_per_day)
        for venue in venues:
            add({x_index[i, d]: 1 for i in range(len(f)) if f.iloc[i].venue == venue}, upper=1)
    # No team may play twice within match day + configured full rest days.
    window = minimum_rest_days + 1
    for team in teams:
        for start in range(horizon_days):
            days = range(start, min(horizon_days, start + window))
            add({x_index[i, d]: 1 for i in games[team] for d in days}, upper=1)

    if minimize_travel:
        big_m = horizon_days
        for team in teams:
            nodes = games[team]
            # One predecessor and successor for every match, plus one route start/end.
            for j in nodes:
                add({z_index[team, i, j]: 1 for i in [-1] + nodes if i != j}, 1, 1)
            for i in nodes:
                add({z_index[team, i, j]: 1 for j in nodes + [-2] if j != i}, 1, 1)
            add({z_index[team, -1, j]: 1 for j in nodes}, 1, 1)
            add({z_index[team, i, -2]: 1 for i in nodes}, 1, 1)
            # If arc i->j is active, j must occur later. This also removes subtours.
            for i in nodes:
                for j in nodes:
                    if i == j: continue
                    coefs = {z_index[team, i, j]: big_m}
                    for d in range(horizon_days):
                        coefs[x_index[i, d]] = coefs.get(x_index[i, d], 0) + d
                        coefs[x_index[j, d]] = coefs.get(x_index[j, d], 0) - d
                    add(coefs, upper=big_m - 1)

    model = pulp.LpProblem("IPL_schedule", pulp.LpMinimize)
    variables = [pulp.LpVariable(f"v_{i}", cat="Binary") for i in range(n)]
    model += pulp.lpSum(c[i] * variables[i] for i in range(n))
    for r, (coefs, lo, hi) in enumerate(rows):
        expression = pulp.lpSum(value * variables[col] for col, value in coefs.items())
        if lo is not None: model += expression >= lo, f"lower_{r}"
        if hi is not None: model += expression <= hi, f"upper_{r}"
    # A valid incumbent dramatically improves CBC reliability on the travel MILP.
    if minimum_rest_days == 1 and max_matches_per_day == 1 and horizon_days >= len(f):
        order = _warm_start_order(f)
        if order is not None:
            assigned_day = {fixture: day for day, fixture in enumerate(order)}
            for i in range(len(f)):
                for d in range(horizon_days):
                    variables[x_index[i, d]].setInitialValue(int(assigned_day[i] == d))
            if minimize_travel:
                for team in teams:
                    route = sorted(games[team], key=assigned_day.get)
                    active = {(team, -1, route[0]), (team, route[-1], -2)}
                    active.update((team, a, b) for a, b in zip(route, route[1:]))
                    for key, idx in z_index.items(): variables[idx].setInitialValue(int(key in active))
    started = perf_counter()
    solver = pulp.PULP_CBC_CMD(msg=False, timeLimit=time_limit_seconds, gapRel=0.02,
                              warmStart=True, keepFiles=True)
    model.solve(solver)
    elapsed = perf_counter() - started
    pulp_status = pulp.LpStatus[model.status]
    values = [v.value() for v in variables]
    non_integer = any(value is None or abs(value - round(value)) > 1e-5 for value in values)
    if pulp_status in {"Infeasible", "Unbounded", "Undefined"} or non_integer:
        status = "infeasible" if pulp_status == "Infeasible" else "no_solution"
        return OptimizationResult(status, pd.DataFrame(), None, elapsed, pulp_status)
    assignments = []
    for i, row in f.iterrows():
        d = max(range(horizon_days), key=lambda day: variables[x_index[i, day]].value())
        assignments.append({**row.to_dict(), "date": dates[d]})
    schedule = pd.DataFrame(assignments).sort_values(["date", "venue", "match_id"]).reset_index(drop=True)
    status = "optimal" if model.sol_status == pulp.LpSolutionOptimal else "feasible_time_limit"
    objective = float(pulp.value(model.objective)) if minimize_travel else None
    return OptimizationResult(status, schedule, objective, elapsed, pulp_status)


def validate_schedule(schedule: pd.DataFrame, fixtures: pd.DataFrame,
                      *, minimum_rest_days: int = 1, max_matches_per_day: int = 1) -> list[str]:
    """Independently validate extracted solver output; return all violations."""
    errors = []
    if schedule.empty: return ["Schedule is empty"]
    if schedule.match_id.duplicated().any() or set(schedule.match_id) != set(fixtures.match_id):
        errors.append("Fixtures are missing or duplicated")
    if schedule.groupby("date").size().max() > max_matches_per_day:
        errors.append("Daily match capacity exceeded")
    if schedule.groupby(["date", "venue"]).size().max() > 1:
        errors.append("Venue is double-booked")
    teams = sorted(set(schedule.home_team) | set(schedule.away_team))
    for team in teams:
        dates = schedule.loc[(schedule.home_team == team) | (schedule.away_team == team), "date"].sort_values()
        if dates.duplicated().any(): errors.append(f"{team} is double-booked")
        gaps = dates.diff().dt.days.dropna()
        if (gaps <= minimum_rest_days).any(): errors.append(f"{team} violates minimum rest")
    expected = fixtures.set_index("match_id")[["home_team", "away_team", "venue"]].sort_index()
    actual = schedule.set_index("match_id")[["home_team", "away_team", "venue"]].sort_index()
    if not expected.equals(actual): errors.append("Home/away/venue fixture identity changed")
    return errors
