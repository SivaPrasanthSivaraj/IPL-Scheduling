"""Generate the complete distance matrix from documented stadium coordinates."""

import pandas as pd

from travel import build_distance_table


if __name__ == "__main__":
    coordinates = pd.read_csv("data/venue_coordinates.csv")
    distances = build_distance_table(coordinates)
    distances.to_csv("data/venue_distances.csv", index=False)
    print(f"Wrote {len(distances)} ordered venue pairs")
