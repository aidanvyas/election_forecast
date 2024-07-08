import pandas as pd
import numpy as np
from scipy import stats

def process_data():
    df = pd.read_csv('raw_data/GDPC1.csv')
    df['DATE'] = pd.to_datetime(df['DATE'])
    df = df.set_index('DATE')
    df = df.resample('MS').ffill()

    # right now, the last quarter is being cutoff - essentially the first month is being reported in the quarter, but not months 2 and 3
    df = df.resample('QS').ffill()
    df = df.resample('MS').ffill()

    print(df.head(10))
    print(df.tail(10))



if __name__ == '__main__':
    process_data()