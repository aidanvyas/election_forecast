import pandas as pd
import numpy as np
from scipy import stats


def process_economic_data(gdp_data: str,
                          employment_data: str,
                          income_monthly_data: str,
                          income_quarterly_data: str,
                          inflation_monthly_data: str,
                          inflation_quarterly_data: str,
                          stock_market_data: str) -> pd.DataFrame:
    """
    Process economic data for the model.

    Args:
        gdp_data (str):
            Path to the GDP data.
        employment_data (str):
            Path to the employment data.
        income_monthly_data (str):
            Path to the monthly income data.
        income_quarterly_data (str):
            Path to the quarterly income data.
        inflation_monthly_data (str):
            Path to the monthly inflation data.
        inflation_quarterly_data (str):
            Path to the quarterly inflation data.
        stock_market_data (str):
            Path to the stock market data.

    Returns:
        pd.DataFrame:
            Processed economic data.
    """

    # Read in the csv files.
    growth = pd.read_csv(gdp_data)
    employment = pd.read_csv(employment_data)
    income_monthly = pd.read_csv(income_monthly_data)
    income_quarterly = pd.read_csv(income_quarterly_data)
    inflation_monthly = pd.read_csv(inflation_monthly_data)
    inflation_quarterly = pd.read_csv(inflation_quarterly_data)
    stock_market = pd.read_csv(stock_market_data)

    # Reformat the Date columns.
    growth['DATE'] = pd.to_datetime(growth['DATE'])
    employment['DATE'] = pd.to_datetime(employment['DATE'])
    income_monthly['DATE'] = pd.to_datetime(income_monthly['DATE'])
    income_quarterly['DATE'] = pd.to_datetime(income_quarterly['DATE'])
    inflation_monthly['DATE'] = pd.to_datetime(inflation_monthly['DATE'])
    inflation_quarterly['DATE'] = pd.to_datetime(inflation_quarterly['DATE'])
    stock_market['Date'] = pd.to_datetime(stock_market['Date'], format='%Y%m')

    # Set the Date columns as the index.
    growth = growth.set_index('DATE')
    employment = employment.set_index('DATE')
    income_monthly = income_monthly.set_index('DATE')
    income_quarterly = income_quarterly.set_index('DATE')
    inflation_monthly = inflation_monthly.set_index('DATE')
    inflation_quarterly = inflation_quarterly.set_index('DATE')
    stock_market = stock_market.set_index('Date')

    # Forward fill the quarterly data.
    growth = growth.resample('MS').ffill()
    income_quarterly = income_quarterly.resample('MS').ffill()
    inflation_quarterly = inflation_quarterly.resample('MS').ffill()

    # Deal with the missing data for GDP.
    last_date = growth.index[-1]
    if last_date.month in [1, 4, 7, 10]:
        for i in range(1, 3):
            next_month = last_date + pd.DateOffset(months=i)
            if next_month not in growth.index:
                growth.loc[next_month] = growth.loc[last_date]
        growth = growth.sort_index()

    # Rename the columns.
    employment = employment.rename(columns={'UNRATE': 'Unemployment'})
    income_monthly = income_monthly.rename(columns={'A229RX0': 'RDPI'})
    income_quarterly = income_quarterly.rename(columns={'A229RX0Q048SBEA': 'RDPI'})
    inflation_monthly = inflation_monthly.rename(columns={'PCEPILFE': 'PCE'})
    inflation_quarterly = inflation_quarterly.rename(columns={'PCECTPI': 'PCE'})

    # Merge together the income data.
    income_monthly = income_monthly[income_monthly.index > '1960-01-01']
    income_quarterly = income_quarterly[income_quarterly.index < '1960-01-01']
    income = pd.concat([income_quarterly, income_monthly])

    # Merge together the inflation data.
    inflation_monthly = inflation_monthly[inflation_monthly.index > '1960-01-01']
    inflation_quarterly = inflation_quarterly[inflation_quarterly.index < '1960-01-01']
    inflation = pd.concat([inflation_quarterly, inflation_monthly])

    # Calculate the growth rates and stock market returns.
    growth['RGDP_Growth'] = round(growth['GDPC1'].pct_change(12) * 100, 2)
    income['RDPI_Growth'] = round(income['RDPI'].pct_change(12) * 100, 2)
    inflation['Inflation'] = round(inflation['PCE'].pct_change(12) * 100, 2)
    stock_market['Stock_Market'] = stock_market['Mkt-RF'] + stock_market['RF']

    # Merge all of the data together.
    data = pd.concat([growth['RGDP_Growth'], employment['Unemployment'], income['RDPI_Growth'], inflation['Inflation'], stock_market['Stock_Market']], axis=1, join='inner')
    
    # Return the processed data.
    return data


if __name__ == '__main__':
    processed_economic_data = process_economic_data(gdp_data='raw_data/GDPC1.csv',
                                                    employment_data='raw_data/UNRATE.csv',
                                                    income_monthly_data='raw_data/A229RX0.csv',
                                                    income_quarterly_data='raw_data/A229RX0Q048SBEA.csv',
                                                    inflation_monthly_data='raw_data/PCEPILFE.csv',
                                                    inflation_quarterly_data='raw_data/PCECTPI.csv',
                                                    stock_market_data='raw_data/F-F_Research_Data_Factors 3.csv')
    
    print(processed_economic_data.head())
