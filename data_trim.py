import pandas as pd
# keep the columns detailing year, make, model, and combined mpg
cols = ["year","make","model","comb08"]
# read epa_mpg.csv with selected columns
mpg_table = pd.read_csv("data/epa_mpg.csv", usecols=cols)
# Group by Year, Make, and Model so multiple engine trims average into 1 row per model
mpg_clean = (
    mpg_table.dropna()
    .groupby(["year", "make", "model"], as_index=False)["comb08"]
    .mean()
    .round(1)
)
# write to JSON
mpg_clean.to_json("data/mpg_clean.json", orient="records")