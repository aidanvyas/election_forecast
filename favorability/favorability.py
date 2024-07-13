import pandas as pd
import os


# pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.width', None)

# can i get all of the .csv files in data / favorability / jimmy_carter

# Read in the raw data.
for file in os.listdir("favorability/data/jimmy_carter"):
    # Read in the raw data.
    df = pd.read_csv(f"favorability/data/jimmy_carter/{file}")
    print(df)
    