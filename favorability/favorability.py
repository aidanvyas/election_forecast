import pandas as pd
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import csv
from tkinter import font as tkfont

class PollDisplayApp:
    def __init__(self, master, df, output_filename):
        self.master = master
        self.df = df
        self.output_filename = output_filename
        self.current_index = 0
        self.unique_questions = df['QuestionID'].unique()
        self.processed_data = []
        
        self.master.title("Poll Analysis")
        self.master.geometry("1000x800")
        self.master.configure(bg='#f0f0f0')
        
        self.setup_styles()
        self.create_widgets()
        
        self.show_current_poll()
    
    def setup_styles(self):
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Define colors
        bg_color = '#f0f0f0'
        fg_color = '#333333'
        highlight_color = '#4a90e2'
        
        # Configure styles
        self.style.configure('TFrame', background=bg_color)
        self.style.configure('TLabel', background=bg_color, foreground=fg_color, font=('Helvetica', 14))
        self.style.configure('TButton', font=('Helvetica', 12), background=highlight_color, foreground='white')
        self.style.map('TButton', background=[('active', '#2980b9')])
        self.style.configure('Treeview', font=('Helvetica', 12), rowheight=30, background='white', fieldbackground='white')
        self.style.configure('Treeview.Heading', font=('Helvetica', 14, 'bold'))
        self.style.configure('TEntry', font=('Helvetica', 12))
        
        # Custom style for the question label
        self.style.configure('Question.TLabel', font=('Helvetica', 16, 'bold'), wraplength=900, justify='center')
    
    def create_widgets(self):
        main_frame = ttk.Frame(self.master, padding="40 40 40 40", style='TFrame')
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        self.question_label = ttk.Label(main_frame, style='Question.TLabel')
        self.question_label.pack(pady=(0, 30))
        
        self.tree = ttk.Treeview(main_frame, columns=('Response', 'Percentage'), show='headings', style='Treeview')
        self.tree.heading('Response', text='Response')
        self.tree.heading('Percentage', text='Percentage')
        self.tree.column('Response', width=700)
        self.tree.column('Percentage', width=200, anchor='center')
        self.tree.pack(pady=(0, 30), fill=tk.BOTH, expand=True)
        
        input_frame = ttk.Frame(main_frame, style='TFrame')
        input_frame.pack(fill=tk.X, pady=(0, 30))
        
        labels = ['Approve', 'Disapprove', 'No Opinion']
        self.entries = {}
        for i, label in enumerate(labels):
            ttk.Label(input_frame, text=label, style='TLabel').grid(row=0, column=i, padx=10, pady=5)
            entry = ttk.Entry(input_frame, width=15, font=('Helvetica', 12))
            entry.grid(row=1, column=i, padx=10, pady=5)
            self.entries[label] = entry
        
        button_frame = ttk.Frame(main_frame, style='TFrame')
        button_frame.pack(pady=(0, 20))
        
        self.prev_button = ttk.Button(button_frame, text="Previous", command=self.go_back, width=15)
        self.prev_button.pack(side=tk.LEFT, padx=10)
        
        self.next_button = ttk.Button(button_frame, text="Next", command=self.next_poll, width=15)
        self.next_button.pack(side=tk.LEFT, padx=10)
        
        self.exclude_button = ttk.Button(button_frame, text="Exclude", command=self.exclude_poll, width=15)
        self.exclude_button.pack(side=tk.LEFT, padx=10)
        
        self.status_label = ttk.Label(main_frame, text="", style='TLabel')
        self.status_label.pack(pady=10)
        
        # Modify keyboard shortcuts
        self.master.bind('<Return>', self.handle_return)
        self.master.bind('<Escape>', lambda event: self.exclude_poll())
        
        # Set up tab order
        for entry in self.entries.values():
            entry.bind('<FocusIn>', self.on_entry_focus)
    
    def handle_return(self, event):
        focused_widget = self.master.focus_get()
        
        if isinstance(focused_widget, tk.Entry):
            next_widget = focused_widget.tk_focusNext()
            if next_widget in self.entries.values():
                next_widget.focus_set()
            else:
                # If all fields are filled, move to the next poll
                if self.validate_input():
                    self.next_poll()
        else:
            # If focus is not in an entry, move to the first entry
            first_entry = next(iter(self.entries.values()))
            first_entry.focus_set()

    def on_entry_focus(self, event):
        # Select all text when an entry gets focus
        event.widget.select_range(0, tk.END)

    def show_current_poll(self):
        if self.current_index < len(self.unique_questions):
            current_question = self.unique_questions[self.current_index]
            current_data = self.df[self.df['QuestionID'] == current_question]
            
            self.question_label.config(text=current_data['QuestionTxt'].iloc[0])
            
            self.tree.delete(*self.tree.get_children())
            for _, row in current_data.iterrows():
                self.tree.insert('', 'end', values=(row['RespTxt'], f"{row['RespPct']}%"))
            
            self.status_label.config(text=f"Poll {self.current_index + 1} of {len(self.unique_questions)}")
            
            self.prev_button['state'] = tk.NORMAL if self.current_index > 0 else tk.DISABLED
            self.next_button['state'] = tk.NORMAL
            
            for entry in self.entries.values():
                entry.delete(0, tk.END)
            
            # Set focus to the first entry
            first_entry = next(iter(self.entries.values()))
            first_entry.focus_set()
            first_entry.select_range(0, tk.END)  # Select all text in the first entry
        else:
            self.save_data()
    
    def next_poll(self):
        if self.validate_input():
            self.save_current_poll()
            self.current_index += 1
            self.show_current_poll()
    
    def go_back(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.show_current_poll()
    
    def exclude_poll(self):
        self.current_index += 1
        self.show_current_poll()
    
    def validate_input(self):
        try:
            values = [float(entry.get()) for entry in self.entries.values() if entry.get()]
            if not values:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid Input", "Please ensure all fields are filled with valid numbers.")
            return False
        return True
    
    def save_current_poll(self):
        current_question = self.unique_questions[self.current_index]
        current_data = self.df[self.df['QuestionID'] == current_question].iloc[0]
        
        poll_data = {col: current_data[col] for col in self.df.columns if col not in ['RespTxt', 'RespPct']}
        poll_data.update({k: float(v.get()) for k, v in self.entries.items()})
        
        self.processed_data.append(poll_data)
    
    def save_data(self):
        if not self.processed_data:
            messagebox.showinfo("No Data", "No polls were processed.")
            self.master.quit()
            return
        
        with open(self.output_filename, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=self.processed_data[0].keys())
            writer.writeheader()
            writer.writerows(self.processed_data)
        
        messagebox.showinfo("Data Saved", f"Processed data has been saved to {self.output_filename}")
        self.master.quit()

def main(input_file, output_file):
    df = pd.read_csv(input_file)
    
    root = tk.Tk()
    app = PollDisplayApp(root, df, output_file)
    root.mainloop()

if __name__ == "__main__":
    # main("data/raw_ford_favorable.csv", "data/processed_ford_favorable.csv")
    # main("data/raw_carter_favorable.csv", "data/processed_carter_favorable.csv")
    # main("data/raw_reagan_favorable.csv", "data/processed_reagan_favorable.csv")
    # main("data/raw_mondale_favorable.csv", "data/processed_mondale_favorable.csv")
    # main("data/raw_bush_favorable.csv", "data/processed_bush_sr_favorable.csv")
    # main("data/raw_dukakis_favorable.csv", "data/processed_dukakis_favorable.csv")
    # main("data/raw_clinton_favorable.csv", "data/processed_clinton_favorable.csv")
    # main("data/raw_dole_favorable.csv", "data/processed_dole_favorable.csv")
    # main("data/raw_gore_favorable.csv", "data/processed_gore_favorable.csv")
    # main("data/raw_kerry_favorable.csv", "data/processed_kerry_favorable.csv")
    # main("data/raw_mccain_favorable.csv", "data/processed_mccain_favorable.csv")
    # main("data/raw_obama_favorable.csv", "data/processed_obama_favorable.csv")
    # main("data/raw_romney_favorable.csv", "data/processed_romney_favorable.csv")
    main("data/raw_trump_favorable.csv", "data/processed_trump_favorable.csv")
    # main("data/raw_biden_favorable.csv", "data/processed_biden_favorable.csv
