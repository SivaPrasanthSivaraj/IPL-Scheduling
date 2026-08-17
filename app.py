"""Streamlit UI; all data and OR logic remain in dedicated modules."""

import pandas as pd
import streamlit as st

from fixtures import HOME_VENUES_2019, build_double_round_robin
from optimizer import optimize_schedule, validate_schedule
from preprocessing import clean_matches, get_season_data, load_matches
from statistics import season_summary
from travel import historical_schedule, load_distances, travel_by_team, travel_summary


st.set_page_config(page_title="IPL Scheduling Optimization", layout="wide")
st.title("IPL Tournament Scheduling Optimization")
st.caption("Integer programming · real 2019 IPL league fixtures · great-circle stadium distances")


@st.cache_data
def data():
    matches = clean_matches(load_matches())
    distances = load_distances()
    return matches, distances


matches, distances = data()
dashboard, stats_tab, optimization, results = st.tabs(["Dashboard", "Statistics", "Optimization", "Saved results"])

with dashboard:
    cols = st.columns(4)
    cols[0].metric("Matches", f"{len(matches):,}")
    cols[1].metric("Seasons", matches.season.nunique())
    cols[2].metric("Team labels", len(set(matches.team1) | set(matches.team2)))
    cols[3].metric("Venue labels", matches.venue.nunique())
    st.info("Initial optimization scope: season 12 (2019), league stage only—8 teams and 56 fixtures.")

with stats_tab:
    summary = season_summary(matches)
    st.dataframe(summary, width="stretch", hide_index=True)
    st.bar_chart(summary.set_index("year")[["matches", "venues"]])

with optimization:
    mode = st.radio("Objective", ["Generate feasible schedule", "Minimize total travel"])
    rest = st.slider("Full rest days between matches", 0, 2, 1)
    limit = st.slider("Solver time limit (seconds)", 10, 300, 120, 10)
    if st.button("Run optimization", type="primary"):
        season = get_season_data(matches, 12, league_only=True)
        teams = sorted(set(season.team1) | set(season.team2))
        fixtures = build_double_round_robin(teams, HOME_VENUES_2019)
        with st.spinner("Solving integer program…"):
            solved = optimize_schedule(fixtures, distances, minimum_rest_days=rest,
                minimize_travel=mode.startswith("Minimize"), time_limit_seconds=limit)
        if solved.schedule.empty:
            st.error(f"No solution: {solved.message}")
        else:
            errors = validate_schedule(solved.schedule, fixtures, minimum_rest_days=rest)
            st.success(f"Status: {solved.status}; solved in {solved.solve_seconds:.1f}s; validation violations: {len(errors)}")
            st.dataframe(solved.schedule, width="stretch", hide_index=True)
            if mode.startswith("Minimize"):
                historical = historical_schedule(season, HOME_VENUES_2019)
                before, after = travel_summary(historical, distances), travel_summary(solved.schedule, distances)
                c1, c2 = st.columns(2)
                c1.metric("Historical travel", f"{before['total_travel_km']:,.0f} km")
                c2.metric("Optimized travel", f"{after['total_travel_km']:,.0f} km",
                          delta=f"{after['total_travel_km']-before['total_travel_km']:,.0f} km")
                st.bar_chart(travel_by_team(solved.schedule, distances).set_index("team")["travel_km"])

with results:
    try:
        st.dataframe(pd.read_csv("outputs/historical_vs_optimized.csv"), width="stretch", hide_index=True)
        st.download_button("Download optimized schedule", pd.read_csv("outputs/optimized_schedule.csv").to_csv(index=False), "optimized_schedule.csv")
    except FileNotFoundError:
        st.warning("Run `python run_optimization.py` to create saved results.")
