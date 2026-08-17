"""Run both real-season baselines and persist validated project results."""

from pathlib import Path

import pandas as pd

from fixtures import HOME_VENUES_2019, build_double_round_robin, validate_against_historical
from optimizer import optimize_schedule, validate_schedule
from preprocessing import clean_matches, get_season_data, load_matches
from travel import historical_schedule, load_distances, travel_by_team, travel_summary, validate_distance_coverage


def main() -> None:
    output = Path("outputs")
    output.mkdir(exist_ok=True)
    season = get_season_data(clean_matches(load_matches()), 12, league_only=True)
    teams = sorted(set(season.team1) | set(season.team2))
    fixtures = build_double_round_robin(teams, HOME_VENUES_2019)
    validate_against_historical(fixtures, season)
    distances = load_distances()
    validate_distance_coverage(set(fixtures.venue), distances)

    historical = historical_schedule(season, HOME_VENUES_2019)
    historical.to_csv(output / "historical_2019_league.csv", index=False)
    travel_by_team(historical, distances).to_csv(output / "historical_travel_by_team.csv", index=False)

    feasible = optimize_schedule(fixtures, distances, minimize_travel=False, time_limit_seconds=60)
    errors = validate_schedule(feasible.schedule, fixtures)
    if errors: raise RuntimeError(f"Feasible schedule validation failed: {errors}")
    feasible.schedule.to_csv(output / "feasible_schedule.csv", index=False)

    optimized = optimize_schedule(fixtures, distances, minimize_travel=True, time_limit_seconds=180)
    errors = validate_schedule(optimized.schedule, fixtures)
    if errors: raise RuntimeError(f"Optimized schedule validation failed: {errors}")
    optimized.schedule.to_csv(output / "optimized_schedule.csv", index=False)
    travel_by_team(optimized.schedule, distances).to_csv(output / "optimized_travel_by_team.csv", index=False)

    h, o = travel_summary(historical, distances), travel_summary(optimized.schedule, distances)
    comparison = pd.DataFrame([
        {"metric": "Matches", "historical": len(historical), "optimized": len(optimized.schedule)},
        {"metric": "Total travel (km)", "historical": h["total_travel_km"], "optimized": o["total_travel_km"]},
        {"metric": "Maximum team travel (km)", "historical": h["maximum_team_travel_km"], "optimized": o["maximum_team_travel_km"]},
        {"metric": "Constraint violations", "historical": "baseline not constrained", "optimized": 0},
    ])
    comparison.to_csv(output / "historical_vs_optimized.csv", index=False)
    reduction = 100 * (h["total_travel_km"] - o["total_travel_km"]) / h["total_travel_km"]
    print(f"Feasible model: {feasible.status} in {feasible.solve_seconds:.2f}s")
    print(f"Travel model: {optimized.status} in {optimized.solve_seconds:.2f}s")
    print(comparison.to_string(index=False))
    print(f"Travel reduction: {reduction:.2f}%")


if __name__ == "__main__":
    main()
