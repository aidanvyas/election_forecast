import pandas as pd
import json
import os
from typing import List, Dict
from llm_calls import call_gemini_flash
from datetime import datetime, timedelta
from polling_isValid_gui import run_gui
from polling_isValid_testing import compare_llm_with_final


def format_polling(filename: str, year: int) -> List[Dict[str, str]]:
    """
    Formats general election polling data from a CSV file into a JSON string.

    Args:
        filename (str): The path to the CSV file containing the polling data.
        year (int): The year of the general election.

    Returns:
        List[Dict[str, str]]: A list of dictionaries containing the formatted polling data.
    """

    # Read the polling data from the CSV file.
    df = pd.read_csv(filename)

    # Sort by BegDate, EndDate, and QuestionID.
    df = df.sort_values(['BegDate', 'EndDate', 'QuestionID'])

    # Create a list of dictionaries to store the formatted polling data.
    formatted_data = []

    # Define the election dates for each year.
    election_dates_dictionary = {
        1936: '1936-11-03', 1940: '1940-11-05',1944: '1944-11-07',
        1948: '1948-11-02', 1952: '1952-11-04', 1956: '1956-11-06',
        1960: '1960-11-08', 1964: '1964-11-03', 1968: '1968-11-05',
        1972: '1972-11-07', 1976: '1976-11-02', 1980: '1980-11-04',
        1984: '1984-11-06', 1988: '1988-11-08', 1992: '1992-11-03',
        1996: '1996-11-05', 2000: '2000-11-07', 2004: '2004-11-02',
        2008: '2008-11-04', 2012: '2012-11-06', 2016: '2016-11-08',
        2020: '2020-11-03', 2024: '2024-11-05'
    }
    
    # Convert the 'BegDate' and 'EndDate' columns to datetime objects.
    df['BegDate'] = pd.to_datetime(df['BegDate'])
    df['EndDate'] = pd.to_datetime(df['EndDate'])

    # Define the start and end dates for the election year.
    start_date = datetime.strptime(election_dates_dictionary[year-4], '%Y-%m-%d') + timedelta(days=1) if year != 1936 else None
    end_date = datetime.strptime(election_dates_dictionary[year], '%Y-%m-%d') - timedelta(days=1) if year != 2024 else None

    # Filter the polling data based on the election year.
    if start_date and end_date:
        df = df[(df['BegDate'] >= start_date) & (df['EndDate'] <= end_date)]
    elif start_date:
        df = df[df['BegDate'] >= start_date]
    elif end_date:
        df = df[df['EndDate'] <= end_date]

    # Iterate over the unique question IDs in the polling data.
    for question_id in df['QuestionID'].unique():

        # Filter the polling data for the current question ID.
        question_data = df[df['QuestionID'] == question_id]

        # Create a dictionary to store the formatted question data.
        question_dict = {
            "QuestionID": question_id,
            "QuestionText": question_data['QuestionTxt'].iloc[0],
            "Responses": [
                {
                    "ResponseText": row['RespTxt'],
                    "ResponsePct": row['RespPct']
                } for _, row in question_data.iterrows()
            ]
        }

        # Append the formatted question data to the list.
        formatted_data.append(question_dict)

    # Return the formatted polling data as a list of dictionaries.
    return formatted_data


def create_polls_isValid_system_prompt(candidates: List[str], year: int) -> str:
    """
    Creates a system prompt for checking the validity of a general election poll.

    Args:
        candidates (List[str]): A list of candidate names.
        year (int): The year of the general election.

    Returns:
        str: The system prompt for checking the validity of a general election poll.
    """

    # Ensure candidates list is correctly joined into a string
    candidates_str = ', '.join(candidates)

    return f"""You are a polling analyst for the {year} presidential election between the following candidates: {candidates_str}.
    Your task is to determine whether a given poll is a valid general election poll between the specified candidates.

    Criteria for a valid general election poll:
    1. It asks voters directly who they would vote for in the {year} presidential election.
    2. It includes at least two of the following candidates: {candidates_str} in the response options.
    3. It has at least two different response options with numerical percentages.
    4. It does not present hypothetical scenarios or conditions unrelated to whether the candidates are running.
    - A poll about a hypothetical matchup between candidates who haven't announced their candidacy yet is valid.
    - A poll presenting hypothetical scenarios about external factors (e.g., war, economic changes) is not valid.
    - A poll asking about hypothetical vice presidential candidates that are not the actual chosen candidates is invalid.

    Exclude polls that:
    1. Ask about which candidate will win (rather than who the respondent would vote for).
    2. Ask about favorable media coverage.
    3. Ask about which candidate is more trustworthy, has better leadership qualities, will handle certain issues better, etc.
    4. Have only one response option or no numerical percentages.
    5. Don't include at least two of the specified candidates in the response options.
    6. Have a discrepancy between the candidates mentioned in the question and the response options.
    7. Have unrealistic (i.e., multiple candidates from the same party running for the same position).
    
    Your output should be a JSON object with the following structure:
    {{
        "questionId": string,
        "isValid": boolean,
    }}

    Here are some examples.  Given that the valid polls are obvious, I will be focusing on the examples of invalid polls.
    I will additionally provide an explanation for why each poll is assigned to its respective category.
    You should be able to use this information to determine the validity of the polls in the data you are analyzing.
    However, you should not include the explanations in your output.

    Example #1:
    Input:
    [
        {{
            "QuestionID": "USGALLUP.090636.R01",
            "QuestionText": "Whom do you prefer for President?",
            "Responses": [
                {{
                    "ResponseText": "Roosevelt",
                    "ResponsePct": "49"
                }},
                {{
                    "ResponseText": "Landon",
                    "ResponsePct": "44"
                }},
                {{
                    "ResponseText": "Lemke",
                    "ResponsePct": "5"
                }},
                {{
                    "ResponseText": "Thomas",
                    "ResponsePct": "1"
                }},
                {{
                    "ResponseText": "Others",
                    "ResponsePct": "*"
                }}
            ]
        }},
        {{
            "QuestionID": "USGALLUP.36-053.Q4B",
            "QuestionText": "WHICH (1936 PRESIDENTIAL) CANDIDATE DO YOU THINK WILL WIN IN YOUR STATE?",
            "Responses": [
                {{
                    "ResponseText": "LANDON",
                    "ResponsePct": "36"
                }},
                {{
                    "ResponseText": "ROOSEVELT",
                    "ResponsePct": "63"
                }},
                {{
                    "ResponseText": "LEMKE",
                    "ResponsePct": "1"
                }}
            ]
        }}
    ]

    Output:
    [
        {{
            "questionId": "USGALLUP.090636.R01",
            "isValid": true
        }},
        {{
            "questionId": "USGALLUP.36-053.Q4B",
            "isValid": false
        }}
    ]

    Explanation:
    - The first poll is valid because it directly asks voters who they prefer for President and includes multiple candidates with numerical percentages.
    - The second poll is invalid because it asks about which candidate the respondent thinks will win, rather than who they would vote for.

    Example #2:
    Input:
    [
        {{
            "QuestionID": "USGALLUP.40-201.QKT06",
            "QuestionText": "Suppose Roosevelt and Hull are the Democratic candidates for President and Vice-President--would you prefer to vote for them or for the Republican ticket of Willkie and McNary?",
            "Responses": [
                {{
                    "ResponseText": "Roosevelt and Hull",
                    "ResponsePct": "47"
                }},
                {{
                    "ResponseText": "Willkie and McNary",
                    "ResponsePct": "40"
                }},
                {{
                    "ResponseText": "Undecided",
                    "ResponsePct": "13"
                }}
            ]
        }},
        {{
            "QuestionID": "USPR.56.R03",
            "QuestionText": "If President Roosevelt runs for a third term on the Democratic ticket against Wendell Willkie on the Republican ticket, which one would you prefer?",
            "Responses": [
                {{
                    "ResponseText": "Roosevelt",
                    "ResponsePct": "53"
                }},
                {{
                    "ResponseText": "Dewey",
                    "ResponsePct": "25"
                }},
                {{
                    "ResponseText": "No opinion",
                    "ResponsePct": "23"
                }}
            ]
        }},
        {{
            "QuestionID": "USGALLUP.40-216.QK02A",
            "QuestionText": "If the Presidential election were held today, would you vote for the Democratic ticket of Roosevelt and Wallace, or the Republican ticket of Wallace and McNary?",
            "Responses": [
                {{
                    "ResponseText": "Roosevelt and Wallace",
                    "ResponsePct": "53"
                }},
                {{
                    "ResponseText": "Willkie and McNary",
                    "ResponsePct": "47"
                }},
                {{
                    "ResponseText": "Other (vol.)",
                    "ResponsePct": "1"
                }},
                {{
                    "ResponseText": "Undecided",
                    "ResponsePct": "*"
                }}
            ]
        }},
        {{
            "QuestionID": "USGALLUP.40-203.QK02",
            "QuestionText": "If the Presidential election were held today, would you vote for the Republican ticket of Willkie and McNary, or the Democratic ticket of Roosevelt and Wallace?",
            "Responses": [
                {{
                    "ResponseText": "Willkie and McNary",
                    "ResponsePct": "43"
                }},
                {{
                    "ResponseText": "Roosevelt and Wallace",
                    "ResponsePct": "42"
                }},
                {{
                    "ResponseText": "Other",
                    "ResponsePct": "*"
                }},
                {{
                    "ResponseText": "Undecided",
                    "ResponsePct": "14"
                }}
            ]
        }}
    ]

    Output:
    [
        {{
            "questionId": "USGALLUP.40-201.QKT06",
            "isValid": false
        }},
        {{
            "questionId": "USPR.56.R03",
            "isValid": false
        }},
        {{
            "questionId": "USGALLUP.40-216.QK02A",
            "isValid": false
        }},
        {{
            "questionId": "USGALLUP.40-203.QK02",
            "isValid": true
        }}
    ]

    Explanation:
    - The poll is invalid because it presents a hypothetical scenario with candidates that are not actually running for President and Vice-President.
    - The poll is invalid because the candidates mentioned in the question (Roosevelt and Hull) do not match the response options (Roosevelt and Dewey).  Moreover, Dewey is not a candidate in the 1940 election.
    - The poll is invalid because the candidates mentioned in the question (a ticket of Roosevelt and Wallace and a ticket of Wallace and McNary) do not match the response options (Roosevelt and Wallace and Willkie and McNary).
    - The poll is valid because unlike the previous example, the candidates mentioned in the question (Willkie and McNary and Roosevelt and Wallace) match the response options.

    Example #3:
    Input:
    [
        {{
            "QuestionID": "31093632.00012",
            "QuestionText": "(If the election were held today would you vote for (Thomas) Dewey or (Franklin) Roosevelt?) (If Undecided, ask:) Which way are you leaning at the present time--toward Dewey or Roosevelt?",
            "Responses": [
                {{
                    "ResponseText": "Dewey including leaners",
                    "ResponsePct": "49"
                }},
                {{
                    "ResponseText": "Roosevelt including leaners",
                    "ResponsePct": "48"
                }},
                {{
                    "ResponseText": "Undecided",
                    "ResponsePct": "4"
                }}
            ]
        }},
        {{
            "QuestionID": "USGALLUP.42-283.QK08",
            "QuestionText": "Whom would you like to see elected President of the country in 1944?",
            "Responses": [
                {{
                    "ResponseText": "Anyone but F.D.R. (Franklin Delano Roosevelt)",
                    "ResponsePct": "1"
                }},
                {{
                    "ResponseText": "Roosevelt if war is still on",
                    "ResponsePct": "2"
                }},
                {{
                    "ResponseText": "Any Democrat",
                    "ResponsePct": "2"
                }},
                {{
                    "ResponseText": "Roosevelt, Franklin D.",
                    "ResponsePct": "20"
                }},
                {{
                    "ResponseText": "Willkie, Wendell",
                    "ResponsePct": "14"
                }},
                {{
                    "ResponseText": "Dewey, Thomas",
                    "ResponsePct": "11"
                }},
                {{
                    "ResponseText": "Wallace, Henry",
                    "ResponsePct": "3"
                }},
                {{
                    "ResponseText": "Bricker, John",
                    "ResponsePct": "1"
                }},
                {{
                    "ResponseText": "MacArthur",
                    "ResponsePct": "1"
                }},
                {{
                    "ResponseText": "Other",
                    "ResponsePct": "5"
                }},
                {{
                    "ResponseText": "No answer",
                    "ResponsePct": "40"
                }}
            ]
        }},
        {{
            "QuestionID": "USGALLUP.44-319.QT04A",
            "QuestionText": "Will you look over all these possible candidates and tell me which one man you'd like to see as the next President of the United States?... Democratic: Hull, Roosevelt, Wallace, Republican: Dewey, Bricker or Stassen?",
            "Responses": [
                {{
                    "ResponseText": "Hull",
                    "ResponsePct": "3"
                }},
                {{
                    "ResponseText": "Roosevelt",
                    "ResponsePct": "48"
                }},
                {{
                    "ResponseText": "Wallace",
                    "ResponsePct": "2"
                }},
                {{
                    "ResponseText": "Dewey",
                    "ResponsePct": "36"
                }},
                {{
                    "ResponseText": "Bricker",
                    "ResponsePct": "7"
                }},
                {{
                    "ResponseText": "Stassen",
                    "ResponsePct": "5"
                }}
            ]
        }}
    ]

    Output:
    [
        {{
            "questionId": "31093632.00012",
            "isValid": true
        }},
        {{
            "questionId": "USGALLUP.42-283.QK08",
            "isValid": false
        }},
        {{
            "questionId": "USGALLUP.44-319.QT04A",
            "isValid": false
        }}
    ]

    Explanation:
    - The poll is valid because it directly asks voters who they would vote for -- it's okay that it includes leaners in the response options.
    - The poll is invalid because it includes multiple candidates from the same party (Wendell Willkie and Thomas Dewey) and (Franklin D. Roosevelt and Henry Wallace) running for the same position.
    - The poll is invalid because it includes multiple candidates from the same party (Thomas Dewey, John Bricker, and Harold Stassen) running for the same position, and does not include at least two of the specified candidates in the response options.

    Analyze the poll data provided and determine if it's valid based on these criteria.
    
    Please take a deep breath, focus on the task at hand, think carefully and methodically about the instructions given, and provide accurate and consistent responses.

    Criteria for a valid general election poll:
    1. It asks voters directly who they would vote for in the {year} presidential election.
    2. It includes at least two of the following candidates: {candidates_str} in the response options.
    3. It has at least two different response options with numerical percentages.
    4. It does not present hypothetical scenarios or conditions unrelated to whether the candidates are running.
    - A poll about a hypothetical matchup between candidates who haven't announced their candidacy yet is valid.
    - A poll presenting hypothetical scenarios about external factors (e.g., war, economic changes) is not valid.
    - A poll asking about hypothetical vice presidential candidates that are not the actual chosen candidates is invalid.

    Exclude polls that:
    1. Ask about which candidate will win (rather than who the respondent would vote for).
    2. Ask about favorable media coverage.
    3. Ask about which candidate is more trustworthy, has better leadership qualities, will handle certain issues better, etc.
    4. Have only one response option or no numerical percentages.
    5. Don't include at least two of the specified candidates in the response options.
    6. Have a discrepancy between the candidates mentioned in the question and the response options.
    7. Have unrealistic (i.e., multiple candidates from the same party running for the same position).    

    Your output should be a JSON object with the following structure:
    {{
        "questionId": string,
        "isValid": boolean,
    }}
    """


def process_polls_isValid(formatted_data: List[Dict[str, str]], candidates: List[str], year: int, batch_size: int) -> pd.DataFrame:
    """
    Calls the Gemini Flash API to check the validity of general election polls.

    Args:
        formatted_data (List[Dict[str, str]]): A list of dictionaries containing the formatted polling data.
        candidates (List[str]): A list of candidate names.
        year (int): The year of the general election.
        batch_size (int): The number of polls to process in each API call.

    Returns:
        pd.DataFrame: A DataFrame containing with the isValid field added to each poll.
    """

    # Create a system prompt for checking the validity of the polls.
    system_prompt = create_polls_isValid_system_prompt(candidates, year)

    # Initialize an empty list to store the responses from the Gemini Flash API.
    responses = []

    # Iterate over the formatted data in batches.
    for i in range(0, len(formatted_data), batch_size):

        # Extract a batch of polls from the formatted data.
        batch = formatted_data[i:i+batch_size]

        # Convert the batch of polls to a JSON string.
        batch_json = json.dumps(batch)

        # Call the Gemini Flash API to check the validity of the polls.
        response = call_gemini_flash(batch_json, system_prompt)

        # Append the responses to the list.
        responses.extend(response)

    # Convert the processed polls list into a DataFrame.
    processed_df = pd.DataFrame(responses)

    # Return the processed polls DataFrame.
    return processed_df


def merge_polls_with_validity(filename: str, processed_df: pd.DataFrame):
    """
    Merges the processed poll data with the original poll data and saves the result to a new CSV file.

    Args:
        filename (str): The path to the original CSV file containing the polling data.
        processed_df (pd.DataFrame): A DataFrame containing the processed poll data with the isValid field.

    Returns:
        None
    """

    # Read the original polling data from the CSV file.
    df = pd.read_csv(filename)

    # Merge the processed poll data with the original polling data.
    merged_df = df.merge(processed_df, left_on='QuestionID', right_on='questionId', how='left')

    # Remove any rows with missing values in the isValid column
    merged_df = merged_df.dropna(subset=['isValid'])

    # Drop the questionId column from the merged DataFrame.
    merged_df.drop(columns=['questionId'], inplace=True)

    # Get the base filename without the extension.
    base_filename = os.path.splitext(os.path.basename(filename))[0]
    output_filename = f'data/intermediate/polling/{base_filename}_isvalid_llm.csv'

    # Save the merged DataFrame to a new CSV file.
    merged_df.to_csv(output_filename, index=False)


def main():
    filename = 'data/raw/polling/1936_roosevelt_landon.csv'
    candidates = ['Franklin D. Roosevelt', 'Alf Landon']
    year = 1936
    batch_size = 40

    filename = 'data/raw/polling/1940_roosevelt_willkie.csv'
    candidates = ['Franklin D. Roosevelt', 'Wendell Willkie']
    year = 1940

    filename = 'data/raw/polling/1944_roosevelt_dewey.csv'
    candidates = ['Franklin D. Roosevelt', 'Thomas E. Dewey']
    year = 1944

    filename = 'data/raw/polling/1948_truman_dewey.csv'
    candidates = ['Harry S. Truman', 'Thomas E. Dewey']
    year = 1948

    filename = 'data/raw/polling/1952_stevenson_eisenhower.csv'
    candidates = ['Adlai Stevenson II', 'Dwight D. Eisenhower']
    year = 1952

    filename = 'data/raw/polling/1956_eisenhower_stevenson.csv'
    candidates = ['Dwight D. Eisenhower', 'Adlai Stevenson II']
    year = 1956

    base_filename = os.path.splitext(os.path.basename(filename))[0]
    llm_filename = f'data/intermediate/polling/{base_filename}_isvalid_llm.csv'

    # Format the polling data.
    formatted_data = format_polling(filename, year)

    # Process the polling data using the Gemini Flash API.
    processed_df = process_polls_isValid(formatted_data, candidates, year, batch_size)

    # Merge the processed data with the original polling data.
    merge_polls_with_validity(filename, processed_df)

    # Call the human GUI.
    run_gui(llm_filename)

    # Compare the LLM and final CSV files.
    compare_llm_with_final(llm_filename, llm_filename.replace('llm', 'final'))


if __name__ == "__main__":
    main()
