import tkinter as tk
from tkinter import ttk
import pandas as pd

class SimplePollDataReviewGUI:
    def __init__(self, master, old_file, new_file):
        self.master = master
        self.master.title("Simplified Polling Data Review")
        self.master.geometry("800x600")

        self.old_df = pd.read_csv(old_file)
        self.new_df = pd.read_csv(new_file)

        self.question_ids = self.old_df['QuestionID'].unique().tolist()
        self.current_index = 0

        self.create_widgets()
        self.update_display()

    def create_widgets(self):
        # Question Text
        self.question_text = tk.Text(self.master, height=3, wrap=tk.WORD)
        self.question_text.pack(pady=10, padx=10, fill=tk.X)

        # Old Data Frame
        self.old_data_frame = ttk.LabelFrame(self.master, text="Original Data")
        self.old_data_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

        # New Data Frame
        self.new_data_frame = ttk.LabelFrame(self.master, text="Processed Data")
        self.new_data_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

        # Navigation and Progress
        nav_frame = ttk.Frame(self.master)
        nav_frame.pack(pady=10)

        self.prev_button = ttk.Button(nav_frame, text="Previous", command=self.previous_question)
        self.prev_button.pack(side=tk.LEFT, padx=5)

        self.progress_label = ttk.Label(nav_frame, text="")
        self.progress_label.pack(side=tk.LEFT, padx=20)

        self.next_button = ttk.Button(nav_frame, text="Next", command=self.next_question)
        self.next_button.pack(side=tk.LEFT, padx=5)

    def update_display(self):
        current_question_id = self.question_ids[self.current_index]

        # Clear previous data
        for widget in self.old_data_frame.winfo_children():
            widget.destroy()
        for widget in self.new_data_frame.winfo_children():
            widget.destroy()

        # Update Question Text
        question_row = self.old_df[self.old_df['QuestionID'] == current_question_id].iloc[0]
        self.question_text.delete(1.0, tk.END)
        self.question_text.insert(tk.END, question_row['QuestionTxt'])

        # Update Old Data
        old_rows = self.old_df[self.old_df['QuestionID'] == current_question_id]
        for _, row in old_rows.iterrows():
            ttk.Label(self.old_data_frame, text=f"{row['RespTxt']}: {row['RespPct']}%").pack(anchor="w")

        # Update New Data
        new_row = self.new_df[self.new_df['QuestionID'] == current_question_id].iloc[0]
        study_note_index = new_row.index.get_loc('StudyNote')
        for col in new_row.index[study_note_index + 1:]:
            ttk.Label(self.new_data_frame, text=f"{col}: {new_row[col]}").pack(anchor="w")

        # Update Progress Label
        self.progress_label.config(text=f"{self.current_index + 1} / {len(self.question_ids)} polls viewed")

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
    old_file = "new_data/polling/1940_roosevelt_willkie.csv"
    new_file = "1940_processed.csv"

    root = tk.Tk()
    app = SimplePollDataReviewGUI(root, old_file, new_file)
    root.mainloop()

if __name__ == "__main__":
    main()