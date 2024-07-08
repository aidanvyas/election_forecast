import pandas as pd
import numpy as np
from scipy import stats
import statsmodels.api as sm
from typing import Tuple, List
from scipy.optimize import minimize


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

    # Chnage the date index to only keep the year and month.
    composite_index.index = composite_index.index.strftime('%Y-%m')

    # Return the composite economic index.
    return composite_index


def aggregate_fundamental_data(economic_data: pd.DataFrame,
                               incumbency_data: str,
                               approval_data: str,
                               election_results: str) -> pd.DataFrame:
    """
    Aggregate the fundamental data with the poll data.

    Args:
        economic_data (pd.DataFrame):
            Composite economic index.
        incumbency_data (str):
            Path to the incumbency data.
        approval_data (str):
            Path to the approval data
        election_results (str):
            Path to the election results

    Returns:
        pd.DataFrame:
            Aggregated data.
    """

    # Create a copy of the economic data and read in the other data.
    economic_data = economic_data.copy()
    incumbency = pd.read_csv(incumbency_data)
    approvals = pd.read_csv(approval_data)
    election_results = pd.read_csv(election_results)

    # Calculate the incumbent's share of the two-party vote.
    election_results['Incumbent_Share'] = election_results['Incumbent Party Votes'] / (election_results['Incumbent Party Votes'] + election_results['Challenger Party Votes'])

    # Merge the incumbency, approval, and election results data.
    data = pd.merge(incumbency, approvals, on='Year')
    data = pd.merge(data, election_results[['Year', 'Incumbent_Share']], on='Year')

    # Prepare economic windows for each election.
    economic_windows = []
    for year in data['Year']:
        start_date = f"{year-3}-01"
        end_date = f"{year}-09"
        economic_windows.append(economic_data.loc[start_date:end_date])

    return data, economic_windows


def run_regression(data: pd.DataFrame, economic_windows: List[pd.DataFrame]) -> Tuple[np.ndarray, float]:
    """
    Run an optimized regression to find the best parameters for predicting incumbent party vote share.

    Args:
        data (pd.DataFrame): Merged data containing 'Year', 'Incumbency', 'Net Presidential Approval', and 'Incumbent_Share'.
        economic_windows (List[pd.DataFrame]): List of economic data windows for each election year.

    Returns:
        Tuple[np.ndarray, float]: Optimized parameters and R-squared value.
    """
    def exponential_decay(months: float, lambda_param: float) -> float:
        return lambda_param ** months

    def model_function(params: np.ndarray) -> np.ndarray:
        intercept, incumbency_coef, approval_coef, economic_coef, lambda_param = params
        predictions = []
        for i, year in enumerate(data['Year']):
            # Ensure the index is in datetime format
            economic_windows[i].index = pd.to_datetime(economic_windows[i].index)
            months_until_election = ((pd.to_datetime(f"{year}-11-01") - economic_windows[i].index).days / 30.44).astype(float)
            weights = months_until_election.map(lambda x: exponential_decay(x, lambda_param))
            weighted_economic_index = (economic_windows[i]['Composite_Economic_Index'] * weights).sum() / weights.sum()
            
            prediction = (intercept + 
                          incumbency_coef * data.loc[data['Year'] == year, 'Incumbency'].values[0] +
                          approval_coef * data.loc[data['Year'] == year, 'Net Presidential Approval'].values[0] +
                          economic_coef * weighted_economic_index)
            predictions.append(prediction)
        return np.array(predictions)

    def objective_function(params: np.ndarray) -> float:
        predictions = model_function(params)
        actual = data['Incumbent_Share'].values
        return np.sum((predictions - actual) ** 2)

    initial_params = [0.5, 0.1, 0.001, 0.1, 0.5]  # Initial guess for [intercept, incumbency_coef, approval_coef, economic_coef, lambda_param]
    bounds = [(None, None), (None, None), (None, None), (None, None), (0, 1)]  # Bounds for parameters, lambda must be between 0 and 1
    
    result = minimize(objective_function, initial_params, method='L-BFGS-B', bounds=bounds)
    
    optimized_params = result.x
    
    # Calculate R-squared
    predictions = model_function(optimized_params)
    actual = data['Incumbent_Share'].values
    ss_total = np.sum((actual - np.mean(actual)) ** 2)
    ss_residual = np.sum((actual - predictions) ** 2)
    r_squared = 1 - (ss_residual / ss_total)
    
    return optimized_params, r_squared


if __name__ == '__main__':
    processed_economic_data = process_economic_data(gdp_data='raw_data/GDPC1.csv',
                                                    employment_data='raw_data/UNRATE.csv',
                                                    income_monthly_data='raw_data/A229RX0.csv',
                                                    income_quarterly_data='raw_data/A229RX0Q048SBEA.csv',
                                                    inflation_monthly_data='raw_data/PCEPILFE.csv',
                                                    inflation_quarterly_data='raw_data/PCECTPI.csv',
                                                    stock_market_data='raw_data/F-F_Research_Data_Factors 3.csv')
    composite_economic_index = create_composite_economic_index(processed_economic_data)
    data, economic_windows = aggregate_fundamental_data(economic_data=composite_economic_index,
                                incumbency_data='raw_data/incumbency.csv',
                                approval_data='raw_data/approval.csv',
                                election_results='raw_data/election_results.csv')
    run_regression(data=data, economic_windows=economic_windows)
