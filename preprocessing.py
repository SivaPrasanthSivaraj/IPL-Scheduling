"""Loading and preprocessing for the IPL match-level dataset.

Mappings are explicit and deliberately conservative. The source CSV is never
modified, and franchise identities are not merged across seasons.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd


REQUIRED_COLUMNS = {
    "team1", "team2", "match_date", "venue", "city", "season", "match_type"
}

# These are stadium-name variants, not different physical venues.
VENUE_NORMALIZATION = {
    "M.Chinnaswamy Stadium": "M Chinnaswamy Stadium",
    "Brabourne Stadium, Mumbai": "Brabourne Stadium",
}

# Kept empty intentionally: renamed franchises remain distinct historical labels.
TEAM_NORMALIZATION: dict[str, str] = {}


def load_matches(path: str | Path = "ipl.csv") -> pd.DataFrame:
    """Load the source CSV, validate its schema, and parse match dates."""
    df = pd.read_csv(path)
    missing = REQUIRED_COLUMNS.difference(df.columns)
    if missing:
        raise ValueError(f"Dataset is missing required columns: {sorted(missing)}")
    df = df.copy()
    df["match_date"] = pd.to_datetime(df["match_date"], errors="raise")
    return df


def clean_matches(df: pd.DataFrame) -> pd.DataFrame:
    """Return a cleaned copy while preserving all source columns."""
    cleaned = df.copy()
    for column in ("team1", "team2", "toss_winner", "winner"):
        if column in cleaned:
            cleaned[column] = cleaned[column].replace(TEAM_NORMALIZATION)
    cleaned["venue"] = cleaned["venue"].replace(VENUE_NORMALIZATION)
    return cleaned


def get_season_data(
    df: pd.DataFrame, season: int, *, league_only: bool = False
) -> pd.DataFrame:
    """Filter one season, optionally excluding playoffs, in date/match order."""
    result = df.loc[df["season"].eq(season)].copy()
    if result.empty:
        raise ValueError(f"Season {season!r} is not present in the dataset")
    if league_only:
        result = result.loc[result["match_type"].eq("League")].copy()
    return result.sort_values(["match_date", "match_number"]).reset_index(drop=True)


def optimization_table(df: pd.DataFrame) -> pd.DataFrame:
    """Select and label the fields needed by the later scheduling model."""
    return df[[
        "season", "match_date", "team1", "team2", "venue", "city", "match_type",
        "match_number",
    ]].rename(columns={
        "season": "Season", "match_date": "Date", "team1": "Team1",
        "team2": "Team2", "venue": "Venue", "city": "City",
        "match_type": "MatchType", "match_number": "MatchNumber",
    })
