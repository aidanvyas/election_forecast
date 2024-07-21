import pandas as pd
import numpy as np
from scipy import stats
import statsmodels.api as sm
from typing import Tuple, List
from scipy.optimize import minimize
from scipy.stats import t
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import seaborn as sns


def process_economic_data(gdp_data: str,
                          income_monthly_data: str,
                          income_quarterly_data: str) -> pd.DataFrame:
    """
    Process economic data for the model.

    Args:
        gdp_data (str):
            Path to the GDP data.
        income_monthly_data (str):
            Path to the monthly income data.
        income_quarterly_data (str):
            Path to the quarterly income data.

    Returns:
        pd.DataFrame:
            Processed economic data.
    """

    # Read in the csv files.
    growth = pd.read_csv(gdp_data)
    income_monthly = pd.read_csv(income_monthly_data)
    income_quarterly = pd.read_csv(income_quarterly_data)

    # Reformat the Date columns.
    growth['DATE'] = pd.to_datetime(growth['DATE'])
    income_monthly['DATE'] = pd.to_datetime(income_monthly['DATE'])
    income_quarterly['DATE'] = pd.to_datetime(income_quarterly['DATE'])

    # Set the Date columns as the index.
    growth = growth.set_index('DATE')
    income_monthly = income_monthly.set_index('DATE')
    income_quarterly = income_quarterly.set_index('DATE')

    # Forward fill the quarterly data.
    growth = growth.resample('MS').ffill()
    income_quarterly = income_quarterly.resample('MS').ffill()

    # Deal with the missing data for GDP.
    last_date = growth.index[-1]
    if last_date.month in [1, 4, 7, 10]:
        for i in range(1, 3):
            next_month = last_date + pd.DateOffset(months=i)
            if next_month not in growth.index:
                growth.loc[next_month] = growth.loc[last_date]
        growth = growth.sort_index()

    # Rename the columns.
    income_monthly = income_monthly.rename(columns={'A229RX0': 'RDPI'})
    income_quarterly = income_quarterly.rename(columns={'A229RX0Q048SBEA': 'RDPI'})

    # Merge together the income data.
    income_monthly = income_monthly[income_monthly.index >= '1960-01-01']
    income_quarterly = income_quarterly[income_quarterly.index < '1960-01-01']
    income = pd.concat([income_quarterly, income_monthly])

    # Calculate the growth rates.
    growth['RGDP_Growth'] = round(growth['GDPC1'].pct_change(12) * 100, 2)
    income['RDPI_Growth'] = round(income['RDPI'].pct_change(12) * 100, 2)

    # Merge all of the data together.
    data = pd.concat([growth['RGDP_Growth'], income['RDPI_Growth']], axis=1, join='inner')

    # Remove any rows with missing data.
    data = data.dropna()
    
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
    pre_2000_data['RDPI_Growth_Z'] = round(stats.zscore(pre_2000_data['RDPI_Growth']), 2)

    # Calculate composite economic index for pre-2000 data.
    pre_2000_data['Composite_Economic_Index'] = (
        pre_2000_data['RGDP_Growth_Z'] +
        pre_2000_data['RDPI_Growth_Z']
    ) / 2
    pre_2000_data['Composite_Economic_Index'] = round(pre_2000_data['Composite_Economic_Index'], 2)

    # Calculate z-scores for post-2000 data using expanding window.
    post_2000_data = data[data.index >= '2000-01-01']
    post_2000_data = post_2000_data.copy()
    for i in range(len(post_2000_data)):
        window_data = data[:post_2000_data.index[i]]
        post_2000_data.loc[post_2000_data.index[i], 'RGDP_Growth_Z'] = round(stats.zscore(window_data['RGDP_Growth']).iloc[-1], 2)
        post_2000_data.loc[post_2000_data.index[i], 'RDPI_Growth_Z'] = round(stats.zscore(window_data['RDPI_Growth']).iloc[-1], 2)

    # Calculate composite economic index for post-2000 data.
    post_2000_data['Composite_Economic_Index'] = (
        post_2000_data['RGDP_Growth_Z'] +
        post_2000_data['RDPI_Growth_Z']
    ) / 2
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
                               favorability_data: str,
                               military_data: str,
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

    # Read in the data.
    incumbency = pd.read_csv(incumbency_data)
    approvals = pd.read_csv(approval_data)
    favorability = pd.read_csv(favorability_data)
    military_deaths = pd.read_csv(military_data)
    election_results = pd.read_csv(election_results)
    
    # Calculate the incumbent's share of the two-party vote.
    election_results['Incumbent_Share'] = election_results['Incumbent Party Votes'] / (
        election_results['Incumbent Party Votes'] + election_results['Challenger Party Votes']
    )

    military_deaths['Deaths'] = (military_deaths['Deaths'] -military_deaths['Deaths'].shift(1))
    military_deaths.at[0, 'Deaths'] = 206.2
    
    # Merge the incumbency, approval, and election results data.
    data = pd.merge(incumbency, approvals, on='Year')
    data = pd.merge(data, favorability, on='Year')
    data = pd.merge(data, military_deaths, on='Year')
    data = pd.merge(data, election_results[['Year', 'Incumbent_Share']], on='Year')

    # Calculate weighted economic index for each election.
    weighted_economic_indices = []
    for year in data['Year']:
        start_date = f"{year}-01"
        end_date = f"{year}-09"
        window = economic_data.loc[start_date:end_date, 'Composite_Economic_Index']       
        weighted_index = window.mean()
        weighted_economic_indices.append(weighted_index)
    
    # Add weighted economic index to the data.
    data['Weighted_Economic_Index'] = weighted_economic_indices
    
    # Return the aggregated data.
    return data


def run_regression(data: pd.DataFrame) -> None:
    """
    Run a series of regressions to predict incumbent party vote share, 
    saving coefficients for each iteration and plotting results.

    Args:
        data (pd.DataFrame):
            Merged data containing 'Year', 'Incumbency', 'Net Presidential Approval', 
            'Incumbent_Share', and 'Weighted_Economic_Index'.

    Returns:
        None.
    """

    # Create a copy of the data.
    data = data.copy()

    # Create the interaction term.
    data['Incumbency * Net Presidential Approval'] = data['Incumbency'] * data['Net Presidential Approval']
    data['Incumbency * Net Favorability Ratings'] = data['Incumbency'] * data['Net Favorability Ratings']
    data['Incumbency * Weighted_Economic_Index'] = data['Incumbency'] * data['Weighted_Economic_Index']
    data['Incumbency * Deaths'] = data['Incumbency'] * data['Deaths']
    
    # Initialize the list to store coefficients.
    years = range(2000, 2021, 4)
    coefficients = []

    # data is from 1976 to 2020
    data = data[data['Year'] >= 1976]

    X = data[['Weighted_Economic_Index', 'Net Favorability Ratings', 'Deaths']]
    X = sm.add_constant(X)
    y = data['Incumbent_Share']

    model = sm.OLS(y, X)
    results = model.fit()

    print(results.summary())

    # Run regressions for each period.
    for year in years:

        # Train the model on all data before the current year.
        train_data = data[data['Year'] < year]
        X_train = train_data[['Net Favorability Ratings', 'Weighted_Economic_Index', 'Deaths']]
        X_train = sm.add_constant(X_train)
        y_train = train_data['Incumbent_Share']

        # Fit the model.
        model = sm.OLS(y_train, X_train)
        results = model.fit()

        # Save coefficients.
        coefficients.append(results.params.to_dict())

    # Save coefficients to a DataFrame.
    coeff_df = pd.DataFrame(coefficients, index=years)
    coeff_df.index.name = 'Year'
    coeff_df.to_csv('results/regression_coefficients.csv')

    # Predict incumbent share for each period.
    predictions = []
    for year in range(1952, 2021, 4):
        if year <= 2000:
            coeffs = coeff_df.loc[2000].to_dict()
            prediction = coeffs['const'] + coeffs['Net Favorability Ratings'] * data.loc[data['Year'] == year, 'Net Favorability Ratings'] + coeffs['Weighted_Economic_Index'] * data.loc[data['Year'] == year, 'Weighted_Economic_Index'] + coeffs['Deaths'] * data.loc[data['Year'] == year, 'Deaths']
            predictions.append(prediction)
        else:
            coeffs = coeff_df.loc[coeff_df.index == year].iloc[-1].to_dict()
            prediction = coeffs['const'] + coeffs['Net Favorability Ratings'] * data.loc[data['Year'] == year, 'Net Favorability Ratings'] + coeffs['Weighted_Economic_Index'] * data.loc[data['Year'] == year, 'Weighted_Economic_Index'] + coeffs['Deaths'] * data.loc[data['Year'] == year, 'Deaths']
            predictions.append(prediction)

    # Calculate absolute error.
    predictions_flat = [float(pred.iloc[0]) for pred in predictions]
    abs_error = np.abs(data['Incumbent_Share'] - predictions_flat)

    # Save predictions and actual values to a DataFrame.
    pred_df = pd.DataFrame({
        'Year': data['Year'],
        'Actual_Incumbent_Share': data['Incumbent_Share'],
        'Predicted_Incumbent_Share': predictions_flat,
        'Error': abs_error,
        'Sample': ['In-sample' if year < 2000 else 'Out-of-sample' for year in data['Year']]
    })
    pred_df.to_csv('results/predictions_and_actuals.csv', index=False)

    print(pred_df)

    # Plot the actual vs predicted incumbent share.
    plt.figure(figsize=(12, 8))

    # Plot in-sample predictions.
    in_sample = pred_df[pred_df['Sample'] == 'In-sample']
    plt.scatter(in_sample['Predicted_Incumbent_Share'], in_sample['Actual_Incumbent_Share'], 
                color='blue', label='In-Sample', zorder=2)

    # Plot out-of-sample predictions.
    out_sample = pred_df[pred_df['Sample'] == 'Out-of-sample']
    plt.scatter(out_sample['Predicted_Incumbent_Share'], out_sample['Actual_Incumbent_Share'], 
                color='red', label='Out-of-Sample', zorder=2)

    # Add year labels to each point.
    for _, row in pred_df.iterrows():
        plt.annotate(str(int(row['Year'])), 
                    (row['Predicted_Incumbent_Share'], row['Actual_Incumbent_Share']),
                    xytext=(5, 5), textcoords='offset points')

    # Add line of perfect fit.
    min_val = min(pred_df['Predicted_Incumbent_Share'].min(), pred_df['Actual_Incumbent_Share'].min())
    max_val = max(pred_df['Predicted_Incumbent_Share'].max(), pred_df['Actual_Incumbent_Share'].max())
    plt.plot([min_val, max_val], [min_val, max_val], color='green', linestyle='--', 
            label='Line of Perfect Fit', zorder=1)

    # Add labels and title.
    plt.xlabel('Predicted Incumbent Share')
    plt.ylabel('Actual Incumbent Share')
    plt.title('Actual vs Predicted Incumbent Share in Presidential Elections')
    plt.legend()
    plt.grid(True, linestyle=':', alpha=0.7)

    # Ensure the aspect ratio is equal.
    plt.gca().set_aspect('equal', adjustable='box')

    # Save the plot.
    plt.tight_layout()
    plt.savefig('results/incumbent_share_prediction_plot.png', dpi=300)
    plt.close()


def process_polling_averages(old_polling_data: str,
                             recent_polling_data: str) -> pd.DataFrame:
    """
    Process polling data for the model.

    Args:
        old_polling_data (str):
            Path to the old polling data.
        recent_polling_data (str):
            Path to the recent polling data.

    Returns:
        pd.DataFrame:
            Processed polling data.
    """

    # Load in the polling data.
    old_polling = pd.read_csv(old_polling_data, parse_dates=['modeldate', 'election_date'], 
                     usecols=['cycle', 'state', 'modeldate', 'candidate_name', 'pct_estimate', 'election_date'])
    recent_polling = pd.read_csv(recent_polling_data, parse_dates=['modeldate'], usecols=['cycle', 'state', 'modeldate', 'candidate_name', 'pct_estimate'])

    # Combine the data.
    recent_polling['election_date'] = '11/3/2020'
    recent_polling['election_date'] = pd.to_datetime(recent_polling['election_date'])
    polling_data = pd.concat([old_polling, recent_polling])

    # Keep only the national polling.
    polling_data = polling_data[polling_data['state'] == 'National'].drop(columns=['state'])

    # Define the mapping of incumbents and challengers.
    candidate_mapping = {
        1968: {"Incumbent": "Hubert Humphrey, Jr.", "Challenger": "Richard M. Nixon"},
        1972: {"Incumbent": "Richard M. Nixon", "Challenger": "George S. McGovern"},
        1976: {"Incumbent": "Gerald R. Ford", "Challenger": "Jimmy Carter"},
        1980: {"Incumbent": "Jimmy Carter", "Challenger": "Ronald Reagan"},
        1984: {"Incumbent": "Ronald Reagan", "Challenger": "Walter F. Mondale"},
        1988: {"Incumbent": "George Bush", "Challenger": "Michael S. Dukakis"},
        1992: {"Incumbent": "George Bush", "Challenger": "Bill Clinton"},
        1996: {"Incumbent": "Bill Clinton", "Challenger": "Bob Dole"},
        2000: {"Incumbent": "Al Gore", "Challenger": "George W. Bush"},
        2004: {"Incumbent": "George W. Bush", "Challenger": "John Kerry"},
        2008: {"Incumbent": "John McCain", "Challenger": "Barack Obama"},
        2012: {"Incumbent": "Barack Obama", "Challenger": "Mitt Romney"},
        2016: {"Incumbent": "Hillary Rodham Clinton", "Challenger": "Donald Trump"},
        2020: {"Incumbent": "Donald Trump", "Challenger": "Joseph R. Biden Jr."}
    }

    # Function to assign role (Incumbent or Challenger) based on cycle and candidate name.
    def assign_role(row):
        mapping = candidate_mapping.get(row['cycle'])
        if mapping:
            if row['candidate_name'] == mapping['Incumbent']:
                return 'Incumbent'
            elif row['candidate_name'] == mapping['Challenger']:
                return 'Challenger'
        return 'Other'

    # Apply the role assignment.
    polling_data['role'] = polling_data.apply(assign_role, axis=1)

    # Filter out 'Other' candidates.
    polling_data = polling_data[polling_data['role'] != 'Other']

    # Pivot the dataframe.
    polling_data_pivoted = polling_data.pivot_table(
        index=['cycle', 'modeldate', 'election_date'],
        columns='role',
        values='pct_estimate',
        aggfunc='first'
    ).reset_index()

    # Rename columns.
    polling_data_pivoted = polling_data_pivoted.rename(columns={
        'Incumbent': 'incumbent_pct',
        'Challenger': 'challenger_pct'
    })

    # Ensure all required columns are present.
    required_columns = ['cycle', 'modeldate', 'election_date', 'incumbent_pct', 'challenger_pct']
    for col in required_columns:
        if col not in polling_data_pivoted.columns:
            polling_data_pivoted[col] = None

    # Select and order the columns.
    polling_data_final = polling_data_pivoted[required_columns]

    # Return the processed polling data.
    return polling_data_final


def blend_polling_and_fundamentals(polling_averages: pd.DataFrame,
                                   fundamentals: str) -> None:
    """
    Blend polling and fundamental data to predict incumbent vote share.

    Args:
        polling_averages (pd.DataFrame):
            Processed polling data.
        fundamentals (str):
            Path to the fundamental data.

    Returns:
        None.
    """

    # Load in the fundamental data.
    fundamental_data = pd.read_csv(fundamentals)

    # Calculate time to the election.
    polling_averages['days_to_election'] = (polling_averages['election_date'] - polling_averages['modeldate']).dt.days

    # Merge polling data with fundamental data.
    merged_data = pd.merge(polling_averages, 
                           fundamental_data[['Actual_Incumbent_Share', 'Predicted_Incumbent_Share', 'Year']], 
                           left_on='cycle', right_on='Year')
    
    # Calculate incumbent vote share from polls.
    merged_data['poll_incumbent_vote_share'] = merged_data['incumbent_pct'] / (merged_data['incumbent_pct'] + merged_data['challenger_pct'])

    # print(merged_data)

    merged_data = merged_data[merged_data['days_to_election'] == 0]
    merged_data['blended'] = (merged_data['Predicted_Incumbent_Share'] + merged_data['poll_incumbent_vote_share']) / 2
    merged_data['error'] = np.abs(merged_data['blended'] - merged_data['Actual_Incumbent_Share'])

    # X = merged_data[['Predicted_Incumbent_Share', 'poll_incumbent_vote_share']]
    # y = merged_data['Actual_Incumbent_Share']

    # model = sm.OLS(y, X)
    # results = model.fit()

    # print(results.summary())


    print(merged_data[['Year', 'Predicted_Incumbent_Share', 'poll_incumbent_vote_share', 'blended', 'Actual_Incumbent_Share', 'error']])

    rmse1 = ((merged_data['Predicted_Incumbent_Share'] - merged_data['Actual_Incumbent_Share']) ** 2).mean() ** 0.5
    rmse2 = ((merged_data['poll_incumbent_vote_share'] - merged_data['Actual_Incumbent_Share']) ** 2).mean() ** 0.5
    rmse3 = ((merged_data['blended'] - merged_data['Actual_Incumbent_Share']) ** 2).mean() ** 0.5

    print(rmse1)
    print(rmse2)
    print(rmse3)

    return None
    # Create a list to store the function parameters.
    function_parameters = []

    # Iterate over each election cycle.
    for year in [2000, 2004, 2008, 2012, 2016, 2020]:

        # only get data when the cycle is before 2000.
        merged_data = merged_data[merged_data['cycle'] < year]

        # Initialize DataFrame to store optimized weights.
        time_periods = sorted(merged_data['days_to_election'].unique())
        optimized_weights = pd.DataFrame(index=time_periods, columns=['poll_weight', 'fundamental_weight', 'rmse'])

        # Optimize weights for each time period.
        for time in time_periods:

            # Get the data for the current time period.
            time_slice = merged_data[merged_data['days_to_election'] <= time]
            min_error = np.inf
            best_i = 0
            
            # Iterate over all possible poll weights.
            for i in range(0, 101):

                # Calculate the blended vote share.
                poll_weight = i / 100
                fundamental_weight = 1 - poll_weight
                blended_vote_share = (poll_weight * time_slice['poll_incumbent_vote_share'] + 
                                    fundamental_weight * time_slice['Predicted_Incumbent_Share'])
                
                # Calculate the RMSE.
                rmse = np.sqrt(np.mean((time_slice['Actual_Incumbent_Share'] - blended_vote_share) ** 2))
                
                # Update the minimum error and best poll weight.
                if rmse < min_error:
                    min_error = rmse
                    best_i = i
            
            # Save the optimized weights and RMSE.
            optimized_weights.loc[time, 'poll_weight'] = best_i / 100
            optimized_weights.loc[time, 'fundamental_weight'] = 1 - (best_i / 100)
            optimized_weights.loc[time, 'rmse'] = min_error

        # Get the first and last optimized weights and their respctive days to election.
        first_optimized_weights = optimized_weights.iloc[0]['fundamental_weight']
        last_optimized_weights = optimized_weights.iloc[-1]['fundamental_weight']

        # Define the exponential function.
        A = (last_optimized_weights - first_optimized_weights) / (np.exp(0.01 * max(time_periods)) - 1)
        B = 0.01
        C = first_optimized_weights - A

        print(last_optimized_weights)
        print(first_optimized_weights)

        # Append the function parameters to the list.
        function_parameters.append({
            'Year': year,
            'A': A,
            'B': B,
            'C': C
        })

    # Save the function parameters.
    function_parameters = pd.DataFrame(function_parameters)
    function_parameters.to_csv('results/function_parameters.csv', index=False)


def process_polls():
    return None


if __name__ == '__main__':
    processed_economic_data = process_economic_data(gdp_data='data/GDPC1.csv',
                                                    income_monthly_data='data/A229RX0.csv',
                                                    income_quarterly_data='data/A229RX0Q048SBEA.csv')
    composite_economic_index = create_composite_economic_index(processed_economic_data)
    data = aggregate_fundamental_data(economic_data=composite_economic_index,
                                      incumbency_data='data/incumbency.csv',
                                      approval_data='data/approval.csv',
                                      favorability_data='data/favorability.csv',
                                      military_data='data/military_deaths.csv',
                                      election_results='data/election_results.csv')
    run_regression(data=data)
    # polling_averages = process_polling_averages(old_polling_data='data/pres_pollaverages_1968-2016.csv',
    #                                             recent_polling_data='data/presidential_poll_averages_2020.csv')
    # blend_polling_and_fundamentals(polling_averages=polling_averages,
    #                                fundamentals='results/predictions_and_actuals.csv')
