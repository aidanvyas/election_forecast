import pandas as pd
import json
from typing import List, Dict, Tuple
from common import call_gemini_flash
import tkinter as tk
from tkinter import ttk


def format_polls(filename: str) -> List[Dict]:
    """
    Formats general election polling data from a CSV file into a list of dictionaries.

    Args:
        filename (str): The path to the CSV file containing the polling data.

    Returns:
        List[Dict]: A list of dictionaries containing the formatted polling data.
    """

    # Read the polling data from the CSV file.
    df = pd.read_csv(filename)

    # Create a list of dictionaries to store the formatted polling data.
    formatted_data = []

    # Iterate over the unique question IDs in the polling data.
    for question_id in df['QuestionID'].unique():

        # Filter the polling data for the current question ID.
        question_data = df[df['QuestionID'] == question_id]

        # Create a dictionary to store the formatted question data.
        question_dict = {
            "QuestionID": question_id,
            "QuestionText": question_data['QuestionTxt'].iloc[0],
            "BegDate": question_data['BegDate'].iloc[0],
            "EndDate": question_data['EndDate'].iloc[0],
            "Responses": [
                {
                    "ResponseText": row['RespTxt'],
                    "ResponsePct": row['RespPct']
                } for _, row in question_data.iterrows()
            ]
        }

        # Append the formatted question data to the list.
        formatted_data.append(question_dict)

    # Return the formatted polling data.
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

    return f"""You are a polling analyst for the {year} presidential election. Your task is to determine if a given poll is valid for analysis. A valid poll must meet the following criteria:

    1. It asks voters directly who they would vote for in the {year} presidential election.
    2. It has at least two different response options with numerical percentages.
    3. It does not use leading or biased language that might influence the respondent's answer.
    4. It does not present complex hypothetical scenarios or conditions.
    5. It includes at least two of the following candidates: {', '.join(candidates)}.

    Exclude polls that:
    a) Ask about which candidate will win (rather than who the respondent would vote for).
    b) Ask about favorable media coverage.
    c) Ask about trust on certain issues.
    d) Have only one response option or no numerical percentages.
    e) Don't include at least two of the specified candidates.

    Your output should be a JSON object with the following structure:
    {{
        "questionId": string,
        "isValid": boolean,
    }}

    Analyze the poll data provided and determine if it's valid based on these criteria.

    Examples:

    Valid poll:
    Input:
    {{
        "questionId": "USGALLUP.100436.R06",
        "questionText": "Which candidate do you prefer for President?",
        "responses": [
            {{"ResponseText": "Roosevelt", "ResponsePct": "50"}},
            {{"ResponseText": "Willkie", "ResponsePct": "44"}},
            {{"ResponseText": "Other", "ResponsePct": "6"}}
        ]
    }}

    Output:
    {{
        "questionId": "USGALLUP.100436.R06",
        "isValid": true,
    }}

    Invalid poll:
    Input:
    {{
        "questionId": "USGALLUP.36-053.Q4B",
        "questionText": "WHICH CANDIDATE DO YOU THINK WILL WIN IN YOUR STATE?",
        "responses": [
            {{"ResponseText": "ROOSEVELT", "ResponsePct": "63"}},
            {{"ResponseText": "LANDON", "ResponsePct": "36"}},
            {{"ResponseText": "LEMKE", "ResponsePct": "1"}}
        ]
    }}

    Output:
    {{
        "questionId": "USGALLUP.36-053.Q4B",
        "isValid": false,
    }}

    Analyze the poll data provided and determine if it's valid based on these criteria."""


def process_polls_isValid(formatted_data: List[Dict], candidates: List[str], year: int, batch_size: int) -> pd.DataFrame:
    """
    Calls the Gemini Flash API to check the validity of general election polls.

    Args:
        formatted_data (List[Dict]): A list of dictionaries containing the formatted polling data.
        candidates (List[str]): A list of candidate names.
        year (int): The year of the general election.
        batch_size (int): The number of polls to process in each API call.

    Returns:
        pd.DataFrame: A DataFrame containing with the isValid field added to each poll.
    """

    # Create a system prompt for checking the validity of the polls.
    validity_prompt = create_polls_isValid_system_prompt(candidates, year)

    # Initialize an empty list to store the processed polls.
    processed_polls = []

    # Iterate over the formatted polling data in batches.
    for i in range(0, len(formatted_data), batch_size):

        # Extract a batch of polls from the formatted data.
        batch = formatted_data[i:i+batch_size]

        # Convert the batch of polls to JSON format.
        batch_input = json.dumps([{
            "questionId": poll["QuestionID"],
            "questionText": poll["QuestionText"],
            "responses": poll["Responses"]
        } for poll in batch])

        # Call the Gemini Flash API to check the validity of the polls.
        response = call_gemini_flash(batch_input, validity_prompt)
        
        # Parse the JSON response and update the processed polls.
        try:
            parsed_response = json.loads(response)
            for poll_result in parsed_response:
                poll = next(p for p in batch if p["QuestionID"] == poll_result["questionId"])
                poll["isValid"] = poll_result["isValid"]
                processed_polls.append(poll)
        except json.JSONDecodeError:
            print(f"Failed to parse JSON response for validity check: {response}")

    # Convert the processed polls list into a DataFrame.
    processed_df = pd.DataFrame(processed_polls)

    # Save the processed polls DataFrame to a CSV file.
    processed_df.to_csv("processed_polls.csv", index=False)

    # Return the processed polls DataFrame.
    return processed_df
    

def check_polls_isValid(raw_filename: str, processed_filename: str):
    """
    Create a GUI to check the validity of general election polls.
    """
    class PollViewerApp:
        def __init__(self, master, raw_data, processed_data):
            self.master = master
            self.master.title("Poll Validity Checker")
            self.master.geometry("600x400")

            self.raw_data = raw_data
            self.processed_data = processed_data
            self.current_index = 0

            self.create_widgets()
            self.update_display()

            # Bind arrow keys
            self.master.bind('<Left>', lambda event: self.previous_poll())
            self.master.bind('<Right>', lambda event: self.next_poll())

        def create_widgets(self):
            self.frame = ttk.Frame(self.master, padding="10")
            self.frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

            self.question_text = tk.Text(self.frame, wrap=tk.WORD, height=4, width=60)
            self.question_text.grid(row=0, column=0, columnspan=2, pady=10)

            self.responses_text = tk.Text(self.frame, wrap=tk.WORD, height=10, width=60)
            self.responses_text.grid(row=1, column=0, columnspan=2, pady=10)

            self.validity_label = ttk.Label(self.frame, text="")
            self.validity_label.grid(row=2, column=0, columnspan=2, pady=10)

            self.prev_button = ttk.Button(self.frame, text="Previous", command=self.previous_poll)
            self.prev_button.grid(row=3, column=0, pady=10)

            self.next_button = ttk.Button(self.frame, text="Next", command=self.next_poll)
            self.next_button.grid(row=3, column=1, pady=10)

        def update_display(self):
            question = self.raw_data.iloc[self.current_index]
            processed = self.processed_data[self.processed_data['QuestionID'] == question['QuestionID']].iloc[0]

            self.question_text.delete('1.0', tk.END)
            self.question_text.insert(tk.END, f"Question ID: {question['QuestionID']}\n")
            self.question_text.insert(tk.END, f"Question: {question['QuestionTxt']}\n")

            self.responses_text.delete('1.0', tk.END)
            for i in range(1, 11):  # Assuming max 10 responses
                resp_txt = question.get(f'RespTxt{i}', '')
                resp_pct = question.get(f'RespPct{i}', '')
                if resp_txt and resp_pct:
                    self.responses_text.insert(tk.END, f"{resp_txt}: {resp_pct}%\n")

            validity = "Valid" if processed['isValid'] else "Invalid"
            self.validity_label.config(text=f"Validity: {validity}")

        def previous_poll(self):
            if self.current_index > 0:
                self.current_index -= 1
                self.update_display()

        def next_poll(self):
            if self.current_index < len(self.raw_data) - 1:
                self.current_index += 1
                self.update_display()
            else:
                self.master.quit()

    # Read in the files
    raw_data = pd.read_csv(raw_filename)
    processed_data = pd.read_csv(processed_filename)

    # Create and run the GUI
    root = tk.Tk()
    app = PollViewerApp(root, raw_data, processed_data)
    root.mainloop()


def main():
    # formatted_data = format_polls('raw_data/polling/1936_roosevelt_landon.csv')
    # process_polls_isValid(formatted_data, ['Franklin D. Roosevelt', 'Alf Landon'], 1936, 10)
    check_polls_isValid('raw_data/polling/1936_roosevelt_landon.csv', 'processed_polls.csv')


if __name__ == "__main__":
    main()
