import pandas as pd
import pytest

from preprocessing import clean_matches, get_season_data, load_matches, optimization_table
from statistics import season_summary
from fixtures import HOME_VENUES_2019, build_double_round_robin, validate_against_historical
from optimizer import validate_schedule
from travel import build_distance_table, historical_schedule, validate_distance_coverage


def test_real_dataset_and_selected_season():
    df = clean_matches(load_matches("ipl.csv"))
    selected = get_season_data(df, 12, league_only=True)
    assert len(df) == 1169
    assert len(selected) == 56
    assert len(set(selected.team1) | set(selected.team2)) == 8
    assert selected.city.isna().sum() == 0


def test_optimization_table_schema():
    df = get_season_data(load_matches("ipl.csv"), 12, league_only=True)
    assert optimization_table(df).columns.tolist() == [
        "Season", "Date", "Team1", "Team2", "Venue", "City", "MatchType",
        "MatchNumber",
    ]


def test_season_summary_maps_id_to_actual_year():
    summary = season_summary(load_matches("ipl.csv"))
    row = summary.loc[summary.season.eq(12)].iloc[0]
    assert row.year == 2019
    assert row.matches == 60


def test_unknown_season_is_rejected():
    with pytest.raises(ValueError, match="not present"):
        get_season_data(load_matches("ipl.csv"), 999)


def test_2019_is_double_round_robin_with_eight_home_venues():
    season = get_season_data(clean_matches(load_matches("ipl.csv")), 12, league_only=True)
    fixtures = build_double_round_robin(sorted(set(season.team1) | set(season.team2)), HOME_VENUES_2019)
    validate_against_historical(fixtures, season)
    assert len(fixtures) == 56
    assert fixtures.groupby("home_team").size().eq(7).all()


def test_coordinate_matrix_is_complete_and_symmetric():
    coordinates = pd.read_csv("data/venue_coordinates.csv")
    distances = build_distance_table(coordinates)
    validate_distance_coverage(set(coordinates.venue), distances)
    pivot = distances.pivot(index="from_venue", columns="to_venue", values="distance_km")
    assert (pivot.values == pivot.values.T).all()
    assert (pivot.values.diagonal() == 0).all()


def test_historical_schedule_valid_fixture_identity():
    season = get_season_data(clean_matches(load_matches("ipl.csv")), 12, league_only=True)
    schedule = historical_schedule(season, HOME_VENUES_2019)
    assert len(schedule) == 56
    assert schedule.home_team.value_counts().eq(7).all()
