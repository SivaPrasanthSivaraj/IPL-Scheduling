"""Run the reproducible phase-one dataset inspection and export its results."""

from __future__ import annotations

import argparse
from pathlib import Path

from preprocessing import clean_matches, get_season_data, load_matches, optimization_table
from statistics import missing_value_summary, season_summary, teams_by_season, venues_by_season


SELECTED_SEASON = 12  # The dataset's numeric encoding for 2019.


def run(input_path: Path, output_dir: Path) -> None:
    raw = load_matches(input_path)
    cleaned = clean_matches(raw)
    output_dir.mkdir(parents=True, exist_ok=True)

    summary = season_summary(cleaned)
    summary.to_csv(output_dir / "season_summary.csv", index=False)
    missing_value_summary(raw).to_csv(output_dir / "missing_values.csv", index=False)
    teams_by_season(cleaned).to_csv(output_dir / "teams_by_season.csv", index=False)
    venues_by_season(cleaned).to_csv(output_dir / "venues_by_season.csv", index=False)

    # League fixtures are the initial model scope; playoff participants depend on
    # league results and therefore are not fixed scheduling inputs.
    selected = get_season_data(cleaned, SELECTED_SEASON, league_only=True)
    optimization_table(selected).to_csv(
        output_dir / "selected_season_2019_league.csv", index=False
    )

    print(f"Dataset shape: {raw.shape[0]} rows x {raw.shape[1]} columns")
    print(f"Seasons: {raw['season'].nunique()} (IDs {raw.season.min()}-{raw.season.max()})")
    print(summary.to_string(index=False))
    print(f"\nSelected season: {SELECTED_SEASON} (2019), {len(selected)} league matches")
    print(f"Reports written to: {output_dir.resolve()}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=Path("ipl.csv"))
    parser.add_argument("--output", type=Path, default=Path("outputs"))
    args = parser.parse_args()
    run(args.input, args.output)
