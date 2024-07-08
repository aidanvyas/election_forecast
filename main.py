import pandas as pd
import numpy as np
from scipy import stats

def process_data():
    growth = pd.read_csv('raw_data/GDPC1.csv')
    growth['DATE'] = pd.to_datetime(growth['DATE'])
    growth = growth.set_index('DATE')
    growth = growth.resample('MS').ffill()
    last_date = growth.index[-1]
    if last_date.month in [1, 4, 7, 10]:
        for i in range(1, 3):
            next_month = last_date + pd.DateOffset(months=i)
            if next_month not in growth.index:
                growth.loc[next_month] = growth.loc[last_date]
        growth = growth.sort_index()
    growth['RGDP_Growth'] = round(growth['GDPC1'].pct_change(12) * 100, 2)

    employment = pd.read_csv('raw_data/UNRATE.csv')
    employment['DATE'] = pd.to_datetime(employment['DATE'])
    employment = employment.set_index('DATE')
    # rename
    employment = employment.rename(columns={'UNRATE': 'Unemployment'})

    # Read and process income_monthly data
    income_monthly = pd.read_csv('raw_data/A229RX0.csv')
    income_monthly['DATE'] = pd.to_datetime(income_monthly['DATE'])
    income_monthly = income_monthly.set_index('DATE')
    income_monthly = income_monthly.rename(columns={'A229RX0': 'RDPI'})

    # Read and process income_quarterly data
    income_quarterly = pd.read_csv('raw_data/A229RX0Q048SBEA.csv')
    income_quarterly['DATE'] = pd.to_datetime(income_quarterly['DATE'])
    income_quarterly = income_quarterly.set_index('DATE')
    income_quarterly = income_quarterly.resample('MS').ffill()
    income_quarterly = income_quarterly.rename(columns={'A229RX0Q048SBEA': 'RDPI'})

    # Filter data based on date ranges
    income_monthly = income_monthly[income_monthly.index > '1960-01-01']
    income_quarterly = income_quarterly[income_quarterly.index < '1960-01-01']

    # Combine the two series into the same column
    income = pd.concat([income_quarterly, income_monthly])
    income['RDPI_Growth'] = round(income['RDPI'].pct_change(12) * 100, 2)

    # 
    inflation_monthly = pd.read_csv('raw_data/PCEPILFE.csv')
    inflation_monthly['DATE'] = pd.to_datetime(inflation_monthly['DATE'])
    inflation_monthly = inflation_monthly.set_index('DATE')
    inflation_monthly = inflation_monthly.rename(columns={'PCEPILFE': 'PCE'})

    inflation_quarterly = pd.read_csv('raw_data/PCECTPI.csv')
    inflation_quarterly['DATE'] = pd.to_datetime(inflation_quarterly['DATE'])
    inflation_quarterly = inflation_quarterly.set_index('DATE')
    inflation_quarterly = inflation_quarterly.resample('MS').ffill()
    inflation_quarterly = inflation_quarterly.rename(columns={'PCECTPI': 'PCE'})

    inflation_monthly = inflation_monthly[inflation_monthly.index > '1960-01-01']
    inflation_quarterly = inflation_quarterly[inflation_quarterly.index < '1960-01-01']

    inflation = pd.concat([inflation_quarterly, inflation_monthly])
    inflation['Inflation'] = round(inflation['PCE'].pct_change(12) * 100, 2)

    stock_market = pd.read_csv('raw_data/F-F_Research_Data_Factors 3.csv')
    # this just needs to be the date
    stock_market['Date'] = pd.to_datetime(stock_market['Date'], format='%Y%m')
    stock_market = stock_market.set_index('Date')

    # add together Mkt-RF and RF to get Stock_Market
    stock_market['Stock_Market'] = stock_market['Mkt-RF'] + stock_market['RF']

    # merge all the data together - remove rows with missing data
    data = pd.concat([growth['RGDP_Growth'], employment['Unemployment'], income['RDPI_Growth'], inflation['Inflation'], stock_market['Stock_Market']], axis=1, join='inner')
    
    return data


if __name__ == '__main__':
    processed_economic_data = process_data()
    print(processed_economic_data.head())
