import os
import requests
import pandas as pd
import time
from dotenv import load_dotenv

# Load variables from .env
load_dotenv()
FRED_API_KEY = os.getenv("FRED_API_KEY")
if not FRED_API_KEY:
    raise ValueError("FRED_API_KEY not found! Make sure your .env file is saved.")

# 1. PADD Weekly Gas Series IDs (All Grades, All Formulations)
PADD_GAS_SERIES = {
    "PADD1": "GASALLECW",  # East Coast
    "PADD2": "GASALLMWW",  # Midwest
    "PADD3": "GASALLGCW",  # Gulf Coast
    "PADD4": "GASALLRMW",  # Rocky Mountain (Weekly version!)
    "PADD5": "GASALLWCW",  # West Coast
    "US":    "GASALLW"     # National Average
}

# 2. Map every State + DC to its PADD Region
STATE_TO_PADD = {
    # PADD I: East Coast
    "CT": "PADD1", "DC": "PADD1", "DE": "PADD1", "FL": "PADD1", "GA": "PADD1",
    "MA": "PADD1", "MD": "PADD1", "ME": "PADD1", "NC": "PADD1", "NH": "PADD1",
    "NJ": "PADD1", "NY": "PADD1", "PA": "PADD1", "RI": "PADD1", "SC": "PADD1",
    "VA": "PADD1", "VT": "PADD1", "WV": "PADD1",
    # PADD II: Midwest
    "IA": "PADD2", "IL": "PADD2", "IN": "PADD2", "KS": "PADD2", "KY": "PADD2",
    "MI": "PADD2", "MN": "PADD2", "MO": "PADD2", "ND": "PADD2", "NE": "PADD2",
    "OH": "PADD2", "OK": "PADD2", "SD": "PADD2", "TN": "PADD2", "WI": "PADD2",
    # PADD III: Gulf Coast
    "AL": "PADD3", "AR": "PADD3", "LA": "PADD3", "MS": "PADD3", "NM": "PADD3",
    "TX": "PADD3",
    # PADD IV: Rocky Mountain
    "CO": "PADD4", "ID": "PADD4", "MT": "PADD4", "UT": "PADD4", "WY": "PADD4",
    # PADD V: West Coast
    "AK": "PADD5", "AZ": "PADD5", "CA": "PADD5", "HI": "PADD5", "NV": "PADD5",
    "OR": "PADD5", "WA": "PADD5",
    # National
    "US": "US"
}

def fetch_weekly_gas_summed(series_id):
    """Fetches raw weekly gas prices and computes the 52-week summed price per year."""
    url = "https://api.stlouisfed.org/fred/series/observations"
    params = {
        "series_id": series_id,
        "api_key": FRED_API_KEY,
        "file_type": "json",
        "observation_start": "1993-01-01"
        # No frequency='a' here: we pull raw weekly observations!
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    df = pd.DataFrame(response.json()["observations"])

    df["date"] = pd.to_datetime(df["date"])
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df.dropna(subset=["value"])
    df["year"] = df["date"].dt.year

    # Group by year to get weekly count, raw sum, and mean weekly price
    annual_gas = (
        df.groupby("year", as_index=False)
        .agg(
            weeks_observed=("value", "count"),
            raw_price_sum=("value", "sum"),
            gas_price=("value", "mean")
        )
    )
    # Normalize sum to exactly 52 weeks so 53-Monday years don't skew costs
    annual_gas["price_sum_52wk"] = (
        annual_gas["raw_price_sum"] * (52.0 / annual_gas["weeks_observed"])
    ).round(4)
    annual_gas["gas_price"] = annual_gas["gas_price"].round(3)

    return annual_gas[["year", "gas_price", "price_sum_52wk"]]

def fetch_annual_income(series_id):
    """Fetches annual median household income series from FRED."""
    url = "https://api.stlouisfed.org/fred/series/observations"
    params = {
        "series_id": series_id,
        "api_key": FRED_API_KEY,
        "file_type": "json",
        "observation_start": "1993-01-01",
        "frequency": "a",
        "aggregation_method": "avg"
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    df = pd.DataFrame(response.json()["observations"])

    df["date"] = pd.to_datetime(df["date"])
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df.dropna(subset=["value"])
    df["year"] = df["date"].dt.year

    return df[["year", "value"]]

# --- STEP A: Fetch Weekly PADD & National Gas Series ---
print("Fetching weekly PADD & US gas prices from FRED...")
gas_frames = []
for padd_code, series_id in PADD_GAS_SERIES.items():
    df_gas = fetch_weekly_gas_summed(series_id)
    df_gas["padd"] = padd_code
    gas_frames.append(df_gas)
    time.sleep(0.2)

all_gas_df = pd.concat(gas_frames, ignore_index=True)

# --- STEP B: Fetch State + DC + National Median Income (52 Series) ---
print("Fetching 52 Median Household Income series from FRED...")
income_frames = []
for state_code, padd_code in STATE_TO_PADD.items():
    series_id = "MEHOINUSA646N" if state_code == "US" else f"MEHOINUS{state_code}A646N"
    df_inc = fetch_annual_income(series_id)
    df_inc["state_code"] = state_code
    df_inc["padd"] = padd_code
    df_inc = df_inc.rename(columns={"value": "median_income"})
    income_frames.append(df_inc)
    print(f"  ✓ Loaded {state_code} ({series_id})")
    time.sleep(0.4)

all_income_df = pd.concat(income_frames, ignore_index=True)

# --- STEP C: Merge State Income with PADD Gas Sums by Year ---
fred_merged = (
    pd.merge(all_income_df, all_gas_df, on=["year", "padd"], how="inner")
    .drop(["padd"], axis=1)
)

# Export to JSON
fred_merged.to_json("data/fred_state_macro.json", orient="records")
print(f"\nSuccess! Saved {len(fred_merged)} rows to data/fred_state_macro.json")