import os
import requests
import pandas as pd
import time
from dotenv import load_dotenv

# Load variables from .env
load_dotenv()
# Paste your 32-character FRED API key here (or load from an environment variable)
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

def fetch_annual_series(series_id):
    """Fetches a FRED series and aggregates weekly/monthly observations into annual averages."""
    url = "https://api.stlouisfed.org/fred/series/observations"
    params = {
        "series_id": series_id,
        "api_key": FRED_API_KEY,
        "file_type": "json",
        "Observation_start": "1984-01-01",
        "frequency": "a",
        "aggregation_method": "avg"
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()["observations"]
    
    df = pd.DataFrame(data)
    # Convert date to datetime and value to numeric (ignoring '.' missing values)
    df["date"] = pd.to_datetime(df["date"])
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df.dropna(subset=["value"])
    
    # Extract Year and Aggregate by Annual Mean (handles both weekly gas & annual income!)
    df["year"] = df["date"].dt.year
    # annual_df = df.groupby("year", as_index=False)["value"].mean()
    return df[["year", "value"]]

# --- STEP A: Fetch and Aggregate PADD Gas Prices ---
print("Fetching PADD regional gas prices from FRED...")
gas_frames = []
for padd_code, series_id in PADD_GAS_SERIES.items():
    df_gas = fetch_annual_series(series_id)
    df_gas["padd"] = padd_code
    df_gas = df_gas.rename(columns={"value": "gas_price"})
    df_gas["gas_price"] = df_gas["gas_price"].round(3)
    gas_frames.append(df_gas)
    time.sleep(0.2) # Respect FRED API rate limits

all_gas_df = pd.concat(gas_frames, ignore_index=True)

# --- STEP B: Fetch State Median Household Income (50 States + DC + US) ---
print("Fetching 52 Median Household Income series from FRED...")
income_frames = []
for state_code, padd_code in STATE_TO_PADD.items():
    # FRED pattern: MEHOINUS + 2-letter state code + A646N (Nominal)
    # National US Median Household Income is MEHOINUSA646N
    series_id = "MEHOINUSA646N" if state_code == "US" else f"MEHOINUS{state_code}A646N"
    
    df_inc = fetch_annual_series(series_id)
    df_inc["state_code"] = state_code
    df_inc["padd"] = padd_code
    df_inc = df_inc.rename(columns={"value": "median_income"})
    income_frames.append(df_inc)
    print(f"  ✓ Loaded {state_code} ({series_id})")
    time.sleep(0.5) # Prevents hitting FRED's 120 requests/minute limit

all_income_df = pd.concat(income_frames, ignore_index=True)

# --- STEP C: Merge State Income with PADD Gas Prices by Year ---
fred_merged = pd.merge(
    all_income_df,
    all_gas_df,
    on=["year", "padd"],
    how="inner"
).drop(["padd"], axis = 1)

# Save to JSON
fred_merged.to_json("data/fred_state_macro.json", orient="records")