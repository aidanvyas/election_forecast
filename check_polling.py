import tkinter as tk
from tkinter import ttk
from election_forecast.process_polls import prepare_data_for_gui

class PollViewerApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Poll Viewer")
        self.master.geometry("600x400")

        self.polls = prepare_data_for_gui('raw_data/polling/1936_roosevelt_landon.csv', ['Franklin D. Roosevelt', 'Alf Landon'], 1936, 10)
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
        poll = self.polls[self.current_index]
        
        self.question_text.delete('1.0', tk.END)
        self.question_text.insert(tk.END, f"Question: {poll['QuestionText']}\n")
        self.question_text.insert(tk.END, f"Date: {poll['BegDate']} - {poll['EndDate']}")

        self.responses_text.delete('1.0', tk.END)
        for response in poll['Responses']:
            self.responses_text.insert(tk.END, f"{response['ResponseText']}: {response['ResponsePct']}%\n")

        validity = "Valid" if poll['isValid'] else "Invalid"
        self.validity_label.config(text=f"Validity: {validity}")

    def previous_poll(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.update_display()

    def next_poll(self):
        if self.current_index < len(self.polls) - 1:
            self.current_index += 1
            self.update_display()
        else:
            self.master.quit()

if __name__ == "__main__":
    root = tk.Tk()
    app = PollViewerApp(root)
    root.mainloop()