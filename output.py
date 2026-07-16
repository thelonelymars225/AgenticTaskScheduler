import tkinter as tk
from tkinter import messagebox

class Calculator:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("Calculator")
        self.entry_field = tk.Entry(self.window, width=35, borderwidth=5)
        self.entry_field.grid(row=0, column=0, columnspan=4)

        self.create_buttons()

    def create_buttons(self):
        buttons = [
            '7', '8', '9', '/',
            '4', '5', '6', '*',
            '1', '2', '3', '-',
            '0', '.', '=', '+'
        ]

        row_val = 1
        col_val = 0

        for button in buttons:
            tk.Button(self.window, text=button, width=10, command=lambda button=button: self.click_button(button)).grid(row=row_val, column=col_val)
            col_val += 1
            if col_val > 3:
                col_val = 0
                row_val += 1

        tk.Button(self.window, text="C", width=21, command=self.clear_entry).grid(row=row_val, column=0, columnspan=2)
        tk.Button(self.window, text="Del", width=21, command=self.delete_char).grid(row=row_val, column=2, columnspan=2)

    def click_button(self, button):
        if button == '=':
            try:
                result = str(eval(self.entry_field.get()))
                self.entry_field.delete(0, tk.END)
                self.entry_field.insert(tk.END, result)
            except Exception as e:
                messagebox.showerror("Error", "Invalid input")
                self.entry_field.delete(0, tk.END)
        else:
            self.entry_field.insert(tk.END, button)

    def clear_entry(self):
        self.entry_field.delete(0, tk.END)

    def delete_char(self):
        current = self.entry_field.get()
        self.entry_field.delete(0, tk.END)
        self.entry_field.insert(tk.END, current[:-1])

    def run(self):
        self.window.mainloop()

if __name__ == "__main__":
    calc = Calculator()
    calc.run()
