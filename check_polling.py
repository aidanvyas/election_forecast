import tkinter as tk
from tkinter import ttk
import pandas as pd
from tkinter import font as tkfont

class PollDataReviewGUI:
    def __init__(self, master, old_file, new_file):
        self.master = master
        self.master.title("Polling Data Review")
        self.master.geometry("900x700")
        self.master.configure(bg='#f0f0f0')

        self.old_df = pd.read_csv(old_file)
        self.new_df = pd.read_csv(new_file)
        
        self.question_ids = self.new_df['QuestionID'].tolist()
        self.current_index = 0

        self.create_widgets()
        self.update_display()

    def create_widgets(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TFrame', background='#f0f0f0')
        style.configure('TLabel', background='#f0f0f0', font=('Helvetica', 10))
        style.configure('TButton', font=('Helvetica', 10))

        main_frame = ttk.Frame(self.master, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Question Text
        question_frame = ttk.Frame(main_frame)
        question_frame.pack(pady=10, fill=tk.X)

        self.question_counter = ttk.Label(question_frame, text="", font=('Helvetica', 12, 'bold'))
        self.question_counter.pack(side=tk.TOP, anchor=tk.W)

        self.question_text = tk.Text(question_frame, height=3, wrap=tk.WORD, font=('Helvetica', 12))
        self.question_text.pack(fill=tk.X)

        # Original Data Frame
        self.original_frame = ttk.LabelFrame(main_frame, text="Original Data", padding=10)
        self.original_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

        self.original_canvas = tk.Canvas(self.original_frame, bg='#ffffff')
        self.scrollbar = ttk.Scrollbar(self.original_frame, orient="vertical", command=self.original_canvas.yview)
        self.scrollable_frame = ttk.Frame(self.original_canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.original_canvas.configure(
                scrollregion=self.original_canvas.bbox("all")
            )
        )

        self.original_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.original_canvas.configure(yscrollcommand=self.scrollbar.set)

        self.original_canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # Processed Data Frame
        self.processed_frame = ttk.LabelFrame(main_frame, text="Processed Data", padding=10)
        self.processed_frame.pack(pady=10, padx=10, fill=tk.X)

        self.valid_poll_label = ttk.Label(self.processed_frame, text="Valid Poll:", font=('Helvetica', 10, 'bold'))
        self.valid_poll_label.pack(anchor=tk.W)

        self.candidates_frame = ttk.Frame(self.processed_frame)
        self.candidates_frame.pack(fill=tk.X)

        # Navigation Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=10)

        self.prev_button = ttk.Button(button_frame, text="Previous", command=self.previous_question)
        self.prev_button.pack(side=tk.LEFT, padx=5)

        self.next_button = ttk.Button(button_frame, text="Next", command=self.next_question)
        self.next_button.pack(side=tk.LEFT, padx=5)

    def update_display(self):
        current_question_id = self.question_ids[self.current_index]
        
        # Update counter
        self.question_counter.config(text=f"Question {self.current_index + 1} of {len(self.question_ids)}")

        # Get all rows for the current QuestionID from old_df
        old_rows = self.old_df[self.old_df['QuestionID'] == current_question_id]
        new_row = self.new_df[self.new_df['QuestionID'] == current_question_id].iloc[0]

        # Update Question Text
        self.question_text.delete(1.0, tk.END)
        self.question_text.insert(tk.END, old_rows['QuestionTxt'].iloc[0])

        # Clear previous original data
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        # Update Original Data
        for _, row in old_rows.iterrows():
            resp_frame = ttk.Frame(self.scrollable_frame)
            resp_frame.pack(fill=tk.X, padx=5, pady=2)
            ttk.Label(resp_frame, text=f"Response: {row['RespTxt']}", width=30).pack(side=tk.LEFT, padx=(0, 10))
            ttk.Label(resp_frame, text=f"Percentage: {row['RespPct']}%", width=20).pack(side=tk.LEFT)

        # Update Processed Data
        self.valid_poll_label.config(text=f"Valid Poll: {'Yes' if new_row['validPoll'] else 'No'}")

        # Clear previous candidate labels
        for widget in self.candidates_frame.winfo_children():
            widget.destroy()

        # Add new candidate labels
        candidate_columns = new_row.index[new_row.index.get_loc('StudyNote') + 1:]
        for col in candidate_columns:
            ttk.Label(self.candidates_frame, text=f"{col}: {new_row[col]:.1f}%", font=('Helvetica', 10, 'bold')).pack(anchor=tk.W)

    def previous_question(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.update_display()

    def next_question(self):
        if self.current_index < len(self.question_ids) - 1:
            self.current_index += 1
            self.update_display()
        else:
            self.master.quit()

def main():
    old_file = "new_data/polling/1936_roosevelt_landon.csv"
    new_file = "1936_processed.csv"

    root = tk.Tk()
    app = PollDataReviewGUI(root, old_file, new_file)
    root.mainloop()

if __name__ == "__main__":
    main()
