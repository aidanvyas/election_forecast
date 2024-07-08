import pandas as pd
import numpy as np
from scipy import stats
import statsmodels.api as sm

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
    stock_market['Stock_Market'] = round(stock_market['Mkt-RF'] + stock_market['RF'], 2)

    # Merge all of the data together.
    data = pd.concat([growth['RGDP_Growth'], employment['Unemployment'], income['RDPI_Growth'], inflation['Inflation'], stock_market['Stock_Market']], axis=1, join='inner')
    
    # Return the processed data.
    return data


def create_composite_economic_index(data: pd.DataFrame) -> pd.DataFrame:
    """
    Create a composite economic index.

    Args:
        data (pd.DataFrame):
            Processed economic data.

    Returns:
        pd.DataFrame:
            Composite economic index.
    """

    # Calculate z-scores for pre-2000 data.
    pre_2000_data = data[data.index < '2000-01-01']
    pre_2000_data = pre_2000_data.copy()
    pre_2000_data['RGDP_Growth_Z'] = round(stats.zscore(pre_2000_data['RGDP_Growth']), 2)
    pre_2000_data['Unemployment_Z'] = round(stats.zscore(pre_2000_data['Unemployment']), 2) * -1
    pre_2000_data['RDPI_Growth_Z'] = round(stats.zscore(pre_2000_data['RDPI_Growth']), 2)
    pre_2000_data['Inflation_Z'] = round(stats.zscore(pre_2000_data['Inflation']), 2) * -1
    pre_2000_data['Stock_Market_Z'] = round(stats.zscore(pre_2000_data['Stock_Market']), 2)

    # Calculate composite economic index for pre-2000 data.
    pre_2000_data['Composite_Economic_Index'] = (
        pre_2000_data['RGDP_Growth_Z'] +
        pre_2000_data['Unemployment_Z'] +
        pre_2000_data['RDPI_Growth_Z'] +
        pre_2000_data['Inflation_Z'] +
        pre_2000_data['Stock_Market_Z']
    ) / 5
    pre_2000_data['Composite_Economic_Index'] = round(pre_2000_data['Composite_Economic_Index'], 2)

    # Calculate z-scores for post-2000 data using expanding window.
    post_2000_data = data[data.index >= '2000-01-01']
    post_2000_data = post_2000_data.copy()
    for i in range(len(post_2000_data)):
        window_data = data[:post_2000_data.index[i]]
        post_2000_data.loc[post_2000_data.index[i], 'RGDP_Growth_Z'] = round(stats.zscore(window_data['RGDP_Growth']).iloc[-1], 2)
        post_2000_data.loc[post_2000_data.index[i], 'Unemployment_Z'] = round(stats.zscore(window_data['Unemployment']).iloc[-1], 2) * -1
        post_2000_data.loc[post_2000_data.index[i], 'RDPI_Growth_Z'] = round(stats.zscore(window_data['RDPI_Growth']).iloc[-1], 2)
        post_2000_data.loc[post_2000_data.index[i], 'Inflation_Z'] = round(stats.zscore(window_data['Inflation']).iloc[-1], 2) * -1
        post_2000_data.loc[post_2000_data.index[i], 'Stock_Market_Z'] = round(stats.zscore(window_data['Stock_Market']).iloc[-1], 2)

    # Calculate composite economic index for post-2000 data.
    post_2000_data['Composite_Economic_Index'] = (
        post_2000_data['RGDP_Growth_Z'] +
        post_2000_data['Unemployment_Z'] +
        post_2000_data['RDPI_Growth_Z'] +
        post_2000_data['Inflation_Z'] +
        post_2000_data['Stock_Market_Z']
    ) / 5
    post_2000_data['Composite_Economic_Index'] = round(post_2000_data['Composite_Economic_Index'], 2)

    # Combine pre-2000 and post-2000 data.
    composite_index = pd.concat([pre_2000_data, post_2000_data])

    # Return the composite economic index.
    return composite_index


if __name__ == '__main__':
    processed_economic_data = process_economic_data(gdp_data='raw_data/GDPC1.csv',
                                                    employment_data='raw_data/UNRATE.csv',
                                                    income_monthly_data='raw_data/A229RX0.csv',
                                                    income_quarterly_data='raw_data/A229RX0Q048SBEA.csv',
                                                    inflation_monthly_data='raw_data/PCEPILFE.csv',
                                                    inflation_quarterly_data='raw_data/PCECTPI.csv',
                                                    stock_market_data='raw_data/F-F_Research_Data_Factors 3.csv')
    
    composite_economic_index = create_composite_economic_index(processed_economic_data)
