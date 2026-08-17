"""Venue-distance validation and chronological team-travel metrics."""

from __future__ import annotations

from math import asin, cos, radians, sin, sqrt
from pathlib import Path

import pandas as pd


EARTH_RADIUS_KM = 6371.0088


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance on the mean-radius spherical Earth."""
    dlat, dlon = radians(lat2 - lat1), radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return 2 * EARTH_RADIUS_KM * asin(sqrt(a))


def build_distance_table(coordinates: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for left in coordinates.itertuples(index=False):
        for right in coordinates.itertuples(index=False):
            rows.append({
                "from_venue": left.venue,
                "to_venue": right.venue,
                "distance_km": round(haversine_km(
                    left.latitude, left.longitude, right.latitude, right.longitude
                ), 2),
            })
    return pd.DataFrame(rows)


def load_distances(path: str | Path = "data/venue_distances.csv") -> pd.DataFrame:
    df = pd.read_csv(path)
    required = {"from_venue", "to_venue", "distance_km"}
    if not required.issubset(df.columns):
        raise ValueError(f"Distance file requires columns {sorted(required)}")
    return df


def distance_lookup(distances: pd.DataFrame) -> dict[tuple[str, str], float]:
    return {
        (row.from_venue, row.to_venue): float(row.distance_km)
        for row in distances.itertuples(index=False)
    }


def validate_distance_coverage(venues: set[str], distances: pd.DataFrame) -> None:
    lookup = distance_lookup(distances)
    missing = [(a, b) for a in venues for b in venues if (a, b) not in lookup]
    if missing:
        raise ValueError(f"Distance matrix is missing {len(missing)} ordered pairs")
    if any(lookup[(v, v)] != 0 for v in venues):
        raise ValueError("Self-distances must equal zero")


def travel_by_team(schedule: pd.DataFrame, distances: pd.DataFrame) -> pd.DataFrame:
    lookup = distance_lookup(distances)
    teams = sorted(set(schedule["home_team"]) | set(schedule["away_team"]))
    rows = []
    for team in teams:
        games = schedule.loc[
            schedule["home_team"].eq(team) | schedule["away_team"].eq(team)
        ].sort_values(["date", "match_id"])
        venues = games["venue"].tolist()
        legs = [lookup[(a, b)] for a, b in zip(venues, venues[1:])]
        rows.append({"team": team, "matches": len(games), "travel_km": round(sum(legs), 2)})
    return pd.DataFrame(rows)


def travel_summary(schedule: pd.DataFrame, distances: pd.DataFrame) -> dict[str, float]:
    by_team = travel_by_team(schedule, distances)
    return {
        "total_travel_km": round(float(by_team.travel_km.sum()), 2),
        "maximum_team_travel_km": round(float(by_team.travel_km.max()), 2),
    }


def historical_schedule(matches: pd.DataFrame, home_venues: dict[str, str]) -> pd.DataFrame:
    """Convert historical rows to common schedule schema; venue identifies home."""
    venue_home = {venue: team for team, venue in home_venues.items()}
    rows = []
    for row in matches.sort_values(["match_date", "match_number"]).itertuples():
        home = venue_home[row.venue]
        away = row.team2 if row.team1 == home else row.team1
        rows.append({"match_id": int(row.match_number), "date": row.match_date,
                     "home_team": home, "away_team": away, "venue": row.venue})
    return pd.DataFrame(rows)
