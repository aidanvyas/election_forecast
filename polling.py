from typing import List, Dict
import pandas as pd
import json
import os
import google.generativeai as genai
import logging


def format_general_election_polling(filename: str) -> List[Dict]:
    """
    Formats general election polling data as an input for LLMs.

    Args:
        filename (str): The path to the polling data file.

    Returns:
        List[Dict]: A list of dictionaries containing the formatted
    """

    # Read the polling data.
    df = pd.read_csv(filename)

    # Create a list to store the formatted data.
    formatted_data = []

    # Iterate through each question in the polling data.
    for question_id in df['QuestionID'].unique():

        # Filter the data to the current question.
        question_data = df[df['QuestionID'] == question_id]

        # Extract the question text, begin date, and end date.
        question_text = question_data['QuestionTxt'].iloc[0]
        beg_date = question_data['BegDate'].iloc[0]
        end_date = question_data['EndDate'].iloc[0]

        # Create a dictionary to store the question data.
        question_dict = {
            "QuestionID": question_id,
            "QuestionText": question_text,
            "BegDate": beg_date,
            "EndDate": end_date,
            "Responses": []
        }

        # Iterate through each response for the current question.
        for index, row in question_data.iterrows():

            # Extract the response text and response percentage.
            response_text = row['RespTxt']
            response_pct = row['RespPct']

            # Append the response to the question output.
            question_dict["Responses"].append({
                "ResponseText": response_text,
                "ResponsePct": response_pct
            })

        # Add the question dictionary to the formatted data list.
        formatted_data.append(question_dict)

    # Return the formatted data.
    return formatted_data


def create_system_prompt(candidates: List[str], year: int) -> str:
    """
    Creates a system prompt for the general election polling task.

    Args:
        candidates (List[str]): A list of the main candidates in the election.
        year (int): The year of the election.

    Returns:
        str: A system prompt for the general election polling task.
    """
    candidates_list = ', '.join(candidates)
    candidates_json = ', '.join([f'"{candidate}": number' for candidate in candidates])
    system_prompt = f"""You are a polling analyst for the {year} presidential election. Your task is to analyze multiple polls and provide structured results. Here's what you need to know:

    <candidates>
    {candidates_list}
    </candidates>

    These are the main candidates for the {year} presidential election. Keep them in mind as you analyze the polls.

    Your job is to:

    1. Determine if each poll is valid:
    - A valid poll asks voters who they would vote for in the {year} presidential election.
    - Exclude polls that ask about which candidate will win, has received more favorable media coverage, or is trusted on certain issues.
    - Focus solely on polls about voting intentions for the {year} presidential election.

    2. For valid polls, extract and aggregate voting percentages:
    - Extract voting percentages for the main candidates listed above.
    - Sum percentages for all other responses (e.g., undecided, other, don't know) into an "Other / Undecided" category.
    - If a candidate is not mentioned in a poll, assign them 0%.
    - Report percentages exactly as given in the poll data, without modifications.
    - Do not adjust or normalize percentages. Totals may not add up to 100% due to rounding. Preserve this, especially for the "Other / Undecided" category.
    - Treat asterisks (*) as values less than 0.5%. When encountering an asterisk (*), assign a value of 0% to that response.
    - The "Other / Undecided" category should be the sum of all responses not explicitly listed as main candidates, including those marked with asterisks.
    - The total of all percentages, including "Other / Undecided", may not always add up to 100% due to rounding in the original data. This is expected and should be preserved.

    Your output should be a JSON array of objects, each with the following structure:
    {{
    "questionId": string,
    "validPoll": boolean,
    "results": {{
        {candidates_json},
        "Other / Undecided": number
        }}
    }}

    Here are two examples to guide you:

    Example 1:
    Input:
    {{'QuestionID': 'USGALLUP.090636.R01', 'QuestionText': 'Whom do you prefer for President?', 'BegDate': '08/24/1936', 'EndDate': '08/29/1936', 'Responses': [{{'ResponseText': 'Roosevelt', 'ResponsePct': '49'}}, {{'ResponseText': 'Landon', 'ResponsePct': '44'}}, {{'ResponseText': 'Lemke', 'ResponsePct': '5'}}, {{'ResponseText': 'Thomas', 'ResponsePct': '1'}}, {{'ResponseText': 'Others', 'ResponsePct': '*'}}]}}
    {{'QuestionID': 'USGALLUP.36-053.Q4B', 'QuestionText': 'WHICH (1936 PRESIDENTIAL) CANDIDATE DO YOU THINK WILL WIN IN YOUR STATE?', 'BegDate': '09/28/1936', 'EndDate': '10/2/1936', 'Responses': [{{'ResponseText': 'LANDON', 'ResponsePct': '36'}}, {{'ResponseText': 'ROOSEVELT', 'ResponsePct': '63'}}, {{'ResponseText': 'LEMKE', 'ResponsePct': '1'}}]}}

    Output:
    [
    {{
        "questionId": "USGALLUP.090636.R01",
        "validPoll": true,
        "results": {{
        "Franklin D. Roosevelt": 49,
        "Alf Landon": 44,
        "Other / Undecided": 6
        }}
    }},
    {{
        "questionId": "USGALLUP.36-053.Q4B",
        "validPoll": false,
        "results": {{}}
    }}
    ]

    Example 2:
    Input:
    {{'QuestionID': 'USGALLUP.100436.R06', 'QuestionText': 'Which candidate do you prefer for President?', 'Responses': [{{'ResponseText': 'Roosevelt', 'ResponsePct': '50'}}, {{'ResponseText': 'Landon', 'ResponsePct': '44'}}, {{'ResponseText': 'Lemke', 'ResponsePct': '4'}}, {{'ResponseText': 'Thomas', 'ResponsePct': '1'}}, {{'ResponseText': 'Others', 'ResponsePct': '*'}}]}}

    Output:
    [
    {{
        "questionId": "USGALLUP.100436.R06",
        "validPoll": true,
        "results": {{
        "Franklin D. Roosevelt": 50,
        "Alf Landon": 44,
        "Other / Undecided": 5
        }}
    }}
    ]

    Remember to analyze each poll individually and provide results in the specified JSON format. Ensure that you correctly identify valid polls and accurately report the percentages for each candidate and the "Other / Undecided" category. When calculating the "Other / Undecided" category, include all responses not explicitly listed as main candidates, even if their individual percentages are 0 or marked with an asterisk (*). The sum of all percentages, including "Other / Undecided", should match the sum of the original data, even if it doesn't equal 100%.
    """
    return system_prompt


def call_gemini_flash(llm_input: str, system_prompt: str) -> str:
    """
    Calls the Gemini Flash API with the specified input and system prompt.

    Args:
        llm_input (str): The input data for the LLM.
        system_prompt (str): The system prompt for the LLM.

    Returns:
        str: The response from the Gemini Flash API.
    """

    # Set the API key for Generative AI.
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])

    # Suppress logging from the google libraries.
    logging.getLogger('google.api_core').setLevel(logging.ERROR)
    logging.getLogger('google.auth').setLevel(logging.ERROR)
    logging.getLogger('google.cloud').setLevel(logging.ERROR)

    # Define the generation configuration.
    generation_config = {
        "temperature": 0,
        "top_p": 0.95,
        "top_k": 64,
        "max_output_tokens": 8192,
        "response_mime_type": "application/json",
    }

    # Create a GenerativeModel instance.
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        generation_config=generation_config,
        system_instruction=system_prompt,
    )

    # Start a new chat session.
    chat_session = model.start_chat(history=[])

    # Send the input to the LLM.
    response = chat_session.send_message(llm_input)

    # Return the response text.
    return response.text


def merge_general_election_polling(filename: str, new_df: pd.DataFrame) -> pd.DataFrame:
    """
    Merges the new polling data with the existing DataFrame.

    Args:
        filename (str): The path to the existing polling data file.
        new_df (pd.DataFrame): The new polling data to merge.

    Returns:
        pd.DataFrame: The merged DataFrame.
    """

    # Read the existing DataFrame.
    old_df = pd.read_csv(filename)

    # Get the response columns from the new DataFrame.
    response_columns = [col for col in new_df.columns if col not in ['questionId', 'validPoll']]

    # Drop the response columns from the old DataFrame.
    result_df = old_df.drop(columns=['RespTxt', 'RespPct']).drop_duplicates(subset='QuestionID')

    # Set the QuestionID as the index for the old DataFrame.
    result_df = result_df.set_index('QuestionID')

    # Merge the old and new DataFrames.
    result_df = result_df.reset_index()
    result_df = pd.merge(result_df, new_df, left_on='QuestionID', right_on='questionId', how='left')
    
    # Drop the duplicate QuestionID column.
    result_df = result_df.drop(columns='questionId')

    # Fill missing values in the response columns with 0.
    for col in response_columns:
        result_df[col] = result_df[col].fillna(0)

    # Reorder the columns.
    column_order = ['QuestionID', 'validPoll'] + [col for col in result_df.columns if col not in ['QuestionID', 'validPoll'] + response_columns] + response_columns
    result_df = result_df[column_order]

    # Return the merged DataFrame.
    return result_df


def process_general_election_polling(filename: str, candidates: List[str], year: int, batch_size: int = 10):
    """
    Processes general election polling data and generates system prompts for the task.

    Args:
        filename (str): The path to the polling data file.
        candidates (List[str]): A list of the main candidates in the election.
        year (int): The year of the election.
        batch_size (int): The number of polls to process in each batch.

    Returns:
        None
    """

    # Format the polling data.
    formatted_data = format_general_election_polling(filename)

    # Define the system prompt.
    system_prompt = create_system_prompt(candidates, year)

    # Create a list to store the results.
    results = []

    # Iterate through the formatted data in batches.
    for i in range(0, len(formatted_data), batch_size):

        # Get the current batch of data.
        batch = formatted_data[i:i+batch_size]

        # Convert the batch to a JSON string.
        llm_input = json.dumps(batch)

        # Call the Gemini Flash API.
        response = call_gemini_flash(llm_input, system_prompt)

        # Parse the JSON response and extend the results.
        try:
            parsed_response = json.loads(response)
            if isinstance(parsed_response, list):
                results.extend(parsed_response)
            else:
                results.append(parsed_response)
        except json.JSONDecodeError:
            print(f"Failed to parse JSON response: {response}")

    # Flatten the results.
    flattened_data = []
    for item in results:
        flattened_item = {
            "questionId": item["questionId"],
            "validPoll": item["validPoll"]
        }
        flattened_item.update(item["results"])
        flattened_data.append(flattened_item)

    # Create a DataFrame from the flattened data.
    df = pd.DataFrame(flattened_data)

    # Merge the polling data.
    merged_df = merge_general_election_polling(filename, df)

    # Save the merged DataFrame to a CSV file.
    merged_df.to_csv(f'{year}_processed.csv', index=False)


if __name__ == "__main__":
    process_general_election_polling('new_data/polling/1936_roosevelt_landon.csv', ['Franklin D. Roosevelt', 'Alf Landon'], 1936)
    # process_general_election_polling('new_data/polling/1940_roosevelt_willkie.csv', ['Franklin D. Roosevelt', 'Wendell Willkie'], 1940)
