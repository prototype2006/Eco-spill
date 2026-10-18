
import pandas as pd

# Load the hardware dataset
df = pd.read_csv("ecospill_data.csv")

# Clean column names and distance values
df.columns = df.columns.str.strip()
df["Distance_cm"] = pd.to_numeric(
    df["Distance_cm"], errors="coerce"
)

print("Total rows:", len(df))
print("Valid distance readings:", df["Distance_cm"].notna().sum())
print("Missing/invalid distances:", df["Distance_cm"].isna().sum())

# Show the range of valid readings
print("\nDistance statistics:")
print(df["Distance_cm"].describe())

# Check how many records are usable for analysis
valid = df[df["Distance_cm"].between(20, 400)]
print("\nReadings within the sensor's accepted range:", len(valid))

# Show a few valid readings with their timestamps
print("\nSample valid readings:")
print(valid[["Time", "Distance_cm", "Status"]].head(15).to_string(index=False))
