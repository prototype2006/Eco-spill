
import pandas as pd

# Load the existing dataset. Hardware can stay disconnected.
df = pd.read_csv("ecospill_data.csv")

# Remove accidental spaces from column names.
df.columns = df.columns.str.strip()

# Convert distance and timestamp into usable formats.
df["Distance_cm"] = pd.to_numeric(
    df["Distance_cm"], errors="coerce"
)
df["Time"] = pd.to_datetime(
    df["Time"], errors="coerce"
)

# Keep only valid distances and timestamps.
# The current hardware code accepts distances above 20 cm
# and up to 400 cm.
df = df.dropna(subset=["Time", "Distance_cm"])
df = df[df["Distance_cm"].between(20, 400)].copy()

# Sort chronologically before comparing readings.
df = df.sort_values("Time").reset_index(drop=True)

# Calculate changes between consecutive valid readings.
df["Previous_distance_cm"] = df["Distance_cm"].shift(1)
df["Distance_change_cm"] = (
    df["Distance_cm"] - df["Previous_distance_cm"]
)

# Positive change means the measured surface is farther away.
# If the sensor points down from above the liquid, this can
# indicate a falling liquid level.
df["Time_gap_seconds"] = (
    df["Time"].diff().dt.total_seconds()
)

# Save a separate file; preserve the original CSV.
df.to_csv("ecospill_ml_clean.csv", index=False)

print("ML dataset preparation complete!")
print("Clean rows:", len(df))
print("\nDistance summary:")
print(df["Distance_cm"].describe())

print("\nLargest positive distance changes:")
print(
    df.nlargest(10, "Distance_change_cm")[
        ["Time", "Distance_cm", "Distance_change_cm",
         "Time_gap_seconds", "Status"]
    ].to_string(index=False)
)

print("\nSaved to ecospill_ml_clean.csv")
