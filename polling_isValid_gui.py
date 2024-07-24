import tkinter as tk
from tkinter import ttk
import pandas as pd
import os

class PollingDataEvaluationGUI:
    """
    A GUI for evaluating the validity of polling data.
    """

    def __init__(self, master, llm_filename):
        """
        Initialize the PollingDataEvaluationGUI.

        Args:
            master (tk.Tk): The root window.
            llm_filename (str): The filename of the LLM CSV file.

        Returns:
            None
        """

        # Set the window title and size.
        self.master = master
        self.master.title("Polling Data Evaluation")
        self.master.geometry("800x600")
        self.master.configure(bg="white")

        # Read in the LLM CSV file and group the data.
        self.llm_filename = llm_filename
        self.df = pd.read_csv(llm_filename)
        self.grouped_data = self.group_data()
        self.current_index = 0

        # Create the widgets.
        self.create_widgets()
        self.load_current_poll()

        # Bind the keyboard shortcuts.
        self.master.bind('<Left>', lambda e: self.previous_poll())
        self.master.bind('<Right>', lambda e: self.next_poll())
        self.master.bind('<space>', lambda e: self.switch_validity())


    def group_data(self) -> pd.DataFrame:
        """
        Group the polling data by QuestionID.

        Args:
            None
        
        Returns:
            pd.DataFrame: The grouped polling data.
        """

        # Group the data by QuestionID and aggregate the columns.
        grouped = self.df.groupby('QuestionID').agg({
            'QuestionTxt': 'first',
            'RespTxt': list,
            'RespPct': list,
            'isValid': 'first'
        }).reset_index()

        # Return the grouped data.
        return grouped


    def create_widgets(self):
        """
        Create the widgets for the GUI.

        Args:
            None

        Returns:
            None
        """

        # Create a text box to display the question.
        self.question_text = tk.Text(self.master, wrap=tk.WORD, height=5, width=80, bg="white")
        self.question_text.pack(pady=10)

        # Create a text box to display the responses.
        self.responses_text = tk.Text(self.master, wrap=tk.WORD, height=10, width=80, bg="white")
        self.responses_text.pack(pady=10)

        # Create a label to display the validity.
        self.validity_label = tk.Label(self.master, text="", font=("Arial", 14, "bold"), bg="white")
        self.validity_label.pack(pady=10)

        # Create a button to switch the validity.
        self.switch_button = ttk.Button(self.master, text="Switch Validity", command=self.switch_validity)
        self.switch_button.pack(pady=5)

        # Create a frame for the navigation buttons.
        self.navigation_frame = ttk.Frame(self.master)
        self.navigation_frame.pack(pady=10)

        # Create a button to move to the previous poll.
        self.prev_button = ttk.Button(self.navigation_frame, text="Previous", command=self.previous_poll)
        self.prev_button.grid(row=0, column=0, padx=5)

        # Create a button to move to the next poll.
        self.next_button = ttk.Button(self.navigation_frame, text="Next", command=self.next_poll)
        self.next_button.grid(row=0, column=1, padx=5)

        # Create a label to display the progress.
        self.progress_label = tk.Label(self.master, text="", bg="white")
        self.progress_label.pack(pady=5)


    def load_current_poll(self):
        """
        Load the current poll into the GUI.

        Args:
            None

        Returns:
            None
        """

        # Get the current poll from the grouped data.
        current_poll = self.grouped_data.iloc[self.current_index]
        
        # Clear the question text box.
        self.question_text.delete(1.0, tk.END)
        self.question_text.insert(tk.END, f"Question ID: {current_poll['QuestionID']}\n\n")
        self.question_text.insert(tk.END, current_poll['QuestionTxt'])

        # Clear the responses text box.
        self.responses_text.delete(1.0, tk.END)

        # Iterate over the responses and percentages.
        for resp, pct in zip(current_poll['RespTxt'], current_poll['RespPct']):

            # Add the response and percentage to the text box.
            self.responses_text.insert(tk.END, f"{resp}: {pct}%\n")

        # Update the validity label and progress label.
        self.update_validity_label(current_poll['isValid'])
        self.update_progress_label()


    def update_validity_label(self, is_valid):
        """
        Update the validity label with the current validity.

        Args:
            is_valid (bool): The validity of the current poll.

        Returns:
            None
        """

        # Set the text and color based on the validity.
        if pd.isna(is_valid):
            text = "Unknown"
            color = "gray"
        else:
            text = "Valid" if is_valid else "Invalid"
            color = "green" if is_valid else "red"
        
        # Update the validity label.
        self.validity_label.config(text=text, fg=color)


    def update_progress_label(self):
        """
        Update the progress label with the current index and total polls.

        Args:
            None
    
        Returns:
            None
        """

        # Update the progress label with the current index and total polls.
        total_polls = len(self.grouped_data)
        self.progress_label.config(text=f"{self.current_index + 1} / {total_polls} polls")


    def switch_validity(self):
        """
        Switch the validity of the current poll.

        Args:
            None

        Returns:
            None
        """

        # Get the current validity of the poll.
        current_validity = self.grouped_data.loc[self.current_index, 'isValid']

        # Switch the validity of the current poll.
        if pd.isna(current_validity):
            new_validity = True
        else:
            new_validity = not current_validity

        # Update the validity in the grouped data and the GUI.
        self.grouped_data.loc[self.current_index, 'isValid'] = new_validity
        self.update_validity_label(new_validity)


    def previous_poll(self):
        """
        Move to the previous poll if possible.

        Args:
            None

        Returns:
            None
        """

        # Move to the previous poll if possible.
        if self.current_index > 0:
            self.current_index -= 1
            self.load_current_poll()


    def next_poll(self):
        """
        Move to the next poll if possible.

        Args:
            None

        Returns:
            None
        """

        # Move to the next poll if possible.
        if self.current_index < len(self.grouped_data) - 1:
            self.current_index += 1
            self.load_current_poll()
        else:
            self.save_results()
            self.master.quit()

    def save_results(self):
        """
        Save the updated DataFrame to a CSV file.

        Args:
            None

        Returns:
            None
        """

        # Merge the grouped data with the original DataFrame.
        updated_df = self.df.merge(self.grouped_data[['QuestionID', 'isValid']], on='QuestionID', how='left', suffixes=('', '_updated'))
        updated_df['isValid'] = updated_df['isValid_updated']
        updated_df.drop(columns=['isValid_updated'], inplace=True)

        # Get the base and output filenames.
        base_filename = os.path.splitext(os.path.basename(self.llm_filename))[0]
        output_filename = self.llm_filename.replace('llm', 'final')

        # Save the updated DataFrame to a CSV file.
        updated_df.to_csv(output_filename, index=False)


def run_gui(llm_filename):
    """
    Run the PollingDataEvaluationGUI.

    Args:
        llm_filename (str): The filename of the LLM CSV file.

    Returns:
        None
    """

    # Create the root window and GUI.
    root = tk.Tk()
    app = PollingDataEvaluationGUI(root, llm_filename)
    root.mainloop()
