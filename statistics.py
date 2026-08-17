"""Descriptive statistics for the complete historical IPL dataset."""

from __future__ import annotations

import pandas as pd


def season_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Build one auditable summary row per encoded season."""
    rows = []
    for season, group in df.groupby("season", sort=True):
        teams = set(group["team1"]) | set(group["team2"])
        rows.append({
            "season": int(season),
            "year": int(group["match_date"].dt.year.mode().iat[0]),
            "start_date": group["match_date"].min().date().isoformat(),
            "end_date": group["match_date"].max().date().isoformat(),
            "matches": len(group),
            "league_matches": int(group["match_type"].eq("League").sum()),
            "teams": len(teams),
            "venues": group["venue"].nunique(),
            "cities": group["city"].nunique(dropna=True),
            "missing_city": int(group["city"].isna().sum()),
        })
    return pd.DataFrame(rows)


def missing_value_summary(df: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame({
        "column": df.columns,
        "missing": df.isna().sum().values,
        "missing_percent": (df.isna().mean().values * 100).round(2),
    })


def teams_by_season(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for season, group in df.groupby("season", sort=True):
        for team in sorted(set(group["team1"]) | set(group["team2"])):
            rows.append({"season": int(season), "team": team})
    return pd.DataFrame(rows)


def venues_by_season(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby(["season", "venue"], as_index=False)
        .agg(matches=("match_number", "size"), cities=("city", "nunique"))
        .sort_values(["season", "venue"])
        .reset_index(drop=True)
    )
