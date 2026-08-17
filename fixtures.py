"""Derive the 2019 double round-robin inputs from observed league grounds."""

from __future__ import annotations

import pandas as pd


HOME_VENUES_2019 = {
    "Chennai Super Kings": "MA Chidambaram Stadium",
    "Delhi Capitals": "Arun Jaitley Stadium",
    "Kings XI Punjab": "Punjab Cricket Association IS Bindra Stadium",
    "Kolkata Knight Riders": "Eden Gardens",
    "Mumbai Indians": "Wankhede Stadium",
    "Rajasthan Royals": "Sawai Mansingh Stadium",
    "Royal Challengers Bangalore": "M Chinnaswamy Stadium",
    "Sunrisers Hyderabad": "Rajiv Gandhi International Stadium",
}


def build_double_round_robin(teams: list[str], home_venues: dict[str, str]) -> pd.DataFrame:
    """Create one directed home fixture per ordered pair of distinct teams."""
    if set(teams) != set(home_venues):
        raise ValueError("Every team must have exactly one designated home venue")
    rows = []
    match_id = 1
    for home in sorted(teams):
        for away in sorted(teams):
            if home == away:
                continue
            rows.append({
                "match_id": match_id, "home_team": home, "away_team": away,
                "venue": home_venues[home],
            })
            match_id += 1
    return pd.DataFrame(rows)


def validate_against_historical(fixtures: pd.DataFrame, historical: pd.DataFrame) -> None:
    """Confirm the extracted season really is a two-leg round robin."""
    teams = sorted(set(historical["team1"]) | set(historical["team2"]))
    expected_pairs = len(teams) * (len(teams) - 1) // 2
    pair_counts = historical.apply(
        lambda row: tuple(sorted((row["team1"], row["team2"]))), axis=1
    ).value_counts()
    if len(pair_counts) != expected_pairs or not pair_counts.eq(2).all():
        raise ValueError("Historical league stage is not a complete double round robin")
    expected = len(teams) * (len(teams) - 1)
    if len(fixtures) != expected:
        raise ValueError(f"Expected {expected} directed fixtures, found {len(fixtures)}")
