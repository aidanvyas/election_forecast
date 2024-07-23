import pandas as pd
import tkinter as tk
from tkinter import ttk

def check_poll_validity(filename: str) -> None:
    """
    Displays a GUI for viewing poll data and checking the validity of the question.

    Args:
        filename (str): The filename of the poll data CSV file.

    Returns:
        None
    """

    # Load the poll data from the CSV file
    df = pd.read_csv(filename)

    class PollGui:
        def __init__(self, df):
            self.df = df
            self.question_ids = self.df['QuestionID'].unique()
            self.current_question_index = 0

            self.root = tk.Tk()
            self.root.title('Poll Data Viewer')
            self.root.geometry('1000x700')
            self.root.configure(bg='white')

            self.style = ttk.Style()
            self.style.theme_use('clam')
            self.style.configure('TLabel', background='white', font=('Arial', 12))
            self.style.configure('TFrame', background='white')
            self.style.configure('TButton', font=('Arial', 12))

            self.create_widgets()
            self.update_display()

            self.root.bind('<Right>', self.next)
            self.root.bind('<Left>', self.previous)
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

            self.root.mainloop()

        def create_widgets(self):
            # Question Text
            self.question_label = ttk.Label(self.root, wraplength=980, justify="center", font=("Arial", 16, "bold"))
            self.question_label.pack(pady=20)

            # Response Frame
            self.response_frame = ttk.Frame(self.root)
            self.response_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

            # Validity Label
            self.validity_label = ttk.Label(self.root, font=("Arial", 14, "bold"))
            self.validity_label.pack(pady=10)

            # Navigation Buttons
            button_frame = ttk.Frame(self.root)
            button_frame.pack(pady=20)

            self.prev_button = ttk.Button(button_frame, text="Previous", command=self.previous)
            self.prev_button.pack(side=tk.LEFT, padx=10)

            self.next_button = ttk.Button(button_frame, text="Next", command=self.next)
            self.next_button.pack(side=tk.LEFT, padx=10)

            # Progress Tracker
            self.tracker_label = ttk.Label(self.root, font=("Arial", 12))
            self.tracker_label.pack(pady=10)

        def update_display(self):
            question_id = self.question_ids[self.current_question_index]
            question_data = self.df[self.df['QuestionID'] == question_id]

            # Update question text
            question_text = question_data['QuestionTxt'].iloc[0]
            self.question_label.config(text=f"Question ID: {question_id}\n\n{question_text}")

            # Clear previous responses
            for widget in self.response_frame.winfo_children():
                widget.destroy()

            # Display responses
            for _, row in question_data.iterrows():
                response_frame = ttk.Frame(self.response_frame)
                response_frame.pack(fill=tk.X, padx=5, pady=5)

                resp_txt = row['RespTxt']
                resp_pct = row['RespPct']

                ttk.Label(response_frame, text=f"{resp_txt}: {resp_pct}%", font=("Arial", 14)).pack(side=tk.LEFT)

            # Update validity label
            is_valid = question_data['isValid'].iloc[0]
            validity_color = 'green' if is_valid else 'red'
            self.validity_label.config(text=f"Valid: {is_valid}", foreground=validity_color)

            # Update tracker
            total_questions = len(self.question_ids)
            current_question = self.current_question_index + 1
            self.tracker_label.config(text=f"{current_question} / {total_questions} polls")

        def next(self, event=None):
            if self.current_question_index < len(self.question_ids) - 1:
                self.current_question_index += 1
                self.update_display()
            else:
                self.root.destroy()

        def previous(self, event=None):
            if self.current_question_index > 0:
                self.current_question_index -= 1
                self.update_display()

        def on_closing(self):
            self.root.destroy()

    PollGui(df)

