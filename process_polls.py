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

    Args:
        raw_filename (str): The path to the raw polling data CSV file.
        processed_filename (str): The path to the processed polling data CSV file

    Returns:
        None
    """

    class PollViewerApp:

        # Initialize the PollViewerApp class.
        def __init__(self, master, raw_data, processed_data):

            # Initialize the main window.
            self.master = master
            self.master.title("Poll Validity Checker")
            self.master.geometry("600x400")

            # Initialize the polling data and group by question ID.
            self.raw_data = raw_data
            self.processed_data = processed_data
            self.grouped_data = raw_data.groupby('QuestionID')
            self.question_ids = list(self.grouped_data.groups.keys())
            self.current_index = 0

            # Create the GUI widgets.
            self.create_widgets()
            self.update_display()

            # Bind keyboard events for navigation.
            self.master.bind('<Left>', lambda event: self.previous_poll())
            self.master.bind('<Right>', lambda event: self.next_poll())

        # Create the GUI widgets.
        def create_widgets(self):

            # Create the main frame and widgets.
            self.frame = ttk.Frame(self.master, padding="10")
            self.frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

            # Create the question and responses text widgets.
            self.question_text = tk.Text(self.frame, wrap=tk.WORD, height=4, width=60)
            self.question_text.grid(row=0, column=0, columnspan=2, pady=10)

            # Create the responses text widget.
            self.responses_text = tk.Text(self.frame, wrap=tk.WORD, height=10, width=60)
            self.responses_text.grid(row=1, column=0, columnspan=2, pady=10)

            # Create the validity label and navigation buttons.
            self.validity_label = ttk.Label(self.frame, text="")
            self.validity_label.grid(row=2, column=0, columnspan=2, pady=10)

            # Create the progress label and navigation buttons.
            self.prev_button = ttk.Button(self.frame, text="Previous", command=self.previous_poll)
            self.prev_button.grid(row=3, column=0, pady=10)

            # Create the progress label and navigation buttons.
            self.next_button = ttk.Button(self.frame, text="Next", command=self.next_poll)
            self.next_button.grid(row=3, column=1, pady=10)

            # Create the progress label and navigation buttons.
            self.progress_label = ttk.Label(self.master, text="")
            self.progress_label.grid(row=4, column=0, columnspan=2, pady=10)

        # Update the display with the current poll data.
        def update_display(self):

            # Get the question data for the current index.
            question_id = self.question_ids[self.current_index]
            question_group = self.grouped_data.get_group(question_id)
            question = question_group.iloc[0]
            processed = self.processed_data[self.processed_data['QuestionID'] == question_id].iloc[0]

            # Update the question and responses text widgets.
            self.question_text.delete('1.0', tk.END)
            self.question_text.insert(tk.END, f"Question ID: {question_id}\n")
            self.question_text.insert(tk.END, f"Question: {question['QuestionTxt']}\n")

            # Update the responses text widget.
            self.responses_text.delete('1.0', tk.END)
            for _, row in question_group.iterrows():
                response_columns = [col for col in row.index if col.startswith('RespTxt')]
                for col in response_columns:
                    resp_txt = row[col]
                    resp_pct_col = col.replace('RespTxt', 'RespPct')
                    resp_pct = row[resp_pct_col] if resp_pct_col in row else None
                    if pd.notna(resp_txt) and pd.notna(resp_pct):
                        self.responses_text.insert(tk.END, f"{resp_txt}: {resp_pct}%\n")
                    elif pd.notna(resp_txt):
                        self.responses_text.insert(tk.END, f"{resp_txt}: N/A\n")

            # Update the validity label.
            validity = "Valid" if processed['isValid'] else "Invalid"
            self.validity_label.config(text=f"Validity: {validity}")

            # Update the progress label.
            self.progress_label.config(text=f"Poll {self.current_index + 1} / {len(self.question_ids)}")

        # Navigate to the previous poll.
        def previous_poll(self):
            if self.current_index > 0:
                self.current_index -= 1
            else:
                self.current_index = len(self.question_ids) - 1
            self.update_display()

        # Navigate to the next poll.
        def next_poll(self):
            if self.current_index < len(self.question_ids) - 1:
                self.current_index += 1
                self.update_display()
            else:
                self.master.quit()

    # Load the raw and processed polling data.
    raw_data = pd.read_csv(raw_filename)
    processed_data = pd.read_csv(processed_filename)

    # Create the main Tkinter application.
    root = tk.Tk()
    app = PollViewerApp(root, raw_data, processed_data)
    root.mainloop()


def main():
    filename = 'raw_data/polling/1936_roosevelt_landon.csv'
    candidates = ['Franklin D. Roosevelt', 'Alf Landon']
    year = 1936
    batch_size = 10

    filename = 'raw_data/polling/1940_roosevelt_willkie.csv'
    candidates = ['Franklin D. Roosevelt', 'Wendell Willkie']
    year = 1940

    formatted_data = format_polls(filename)
    process_polls_isValid(formatted_data, candidates, year, batch_size)
    check_polls_isValid(filename, "processed_polls.csv")


if __name__ == "__main__":
    main()
