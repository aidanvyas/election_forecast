# Import necessary libraries for GUI creation
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os

# Define the main application class
class PollValidationApp:
    def __init__(self, master):
        self.master = master
        self.master.title('Poll Validation GUI')
        self.filename = ''
        self.data = []
        self.current_index = 0
        self.create_widgets()

    def load_data(self):
        if not os.path.isfile(self.filename):
            messagebox.showerror('Error', 'File not found.')
            return
        with open(self.filename, 'r') as file:
            self.data = json.load(file)
        self.display_current()

    def display_current(self):
        if self.current_index < 0 or self.current_index >= len(self.data):
            messagebox.showerror('Error', 'No more data to display.')
            return
        entry = self.data[self.current_index]
        self.question_id_var.set(entry['QuestionID'])
        self.question_txt_var.set(entry['QuestionTxt'])
        self.resp_txt_var.set(', '.join([resp['RespTxt'] for resp in entry['Responses']]))
        self.resp_pct_var.set(', '.join([str(resp['RespPct']) for resp in entry['Responses']]))

    def mark_valid(self):
        self.data[self.current_index]['Valid'] = True
        self.save_responses()
        self.current_index += 1
        self.display_current()

    def mark_invalid(self):
        self.data[self.current_index]['Valid'] = False
        self.save_responses()
        self.current_index += 1
        self.display_current()

    def previous_entry(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.display_current()

    def save_responses(self):
        with open(self.filename, 'w') as file:
            json.dump(self.data, file)

    def create_widgets(self):
        self.question_id_var = tk.StringVar()
        self.question_txt_var = tk.StringVar()
        self.resp_txt_var = tk.StringVar()
        self.resp_pct_var = tk.StringVar()

        tk.Label(self.master, text='Question ID:').grid(row=0, column=0, sticky='w')
        tk.Entry(self.master, textvariable=self.question_id_var, state='readonly', width=50).grid(row=0, column=1, sticky='ew')

        tk.Label(self.master, text='Question Text:').grid(row=1, column=0, sticky='w')
        tk.Entry(self.master, textvariable=self.question_txt_var, state='readonly', width=50).grid(row=1, column=1, sticky='ew')

        tk.Label(self.master, text='Response Text:').grid(row=2, column=0, sticky='w')
        tk.Entry(self.master, textvariable=self.resp_txt_var, state='readonly', width=50).grid(row=2, column=1, sticky='ew')

        tk.Label(self.master, text='Response Percent:').grid(row=3, column=0, sticky='w')
        tk.Entry(self.master, textvariable=self.resp_pct_var, state='readonly', width=50).grid(row=3, column=1, sticky='ew')

        ttk.Button(self.master, text='Valid', command=self.mark_valid).grid(row=4, column=0)
        ttk.Button(self.master, text='Invalid', command=self.mark_invalid).grid(row=4, column=1)
        ttk.Button(self.master, text='Previous', command=self.previous_entry).grid(row=5, column=0)

        self.master.grid_columnconfigure(1, weight=1)

    def run(self, filename):
        self.filename = filename
        self.load_data()

# Function to start the application
def start_app():
    root = tk.Tk()
    app = PollValidationApp(root)
    filename = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
    if filename:
        app.run(filename)
    root.mainloop()

def validate_polls(filename):
    root = tk.Tk()
    app = PollValidationApp(root)
    app.run(filename)
    root.mainloop()

if __name__ == "__main__":
    start_app()
