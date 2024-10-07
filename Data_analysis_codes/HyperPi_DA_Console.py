from tkinter import filedialog
import tkinter as tk
from tkinter import ttk
import threading
import time
from data_analysis_functions import *

class Data_analysis:
    def __init__(self, root):
        self.root = root
        self.reference = None
        self.flatfield_shape = None
        self.hyperpi_data = None
        self.root.title("Data analysis console for HyperPi project")

        #set GUI frames
        self.root.rowconfigure(0, weight = 3)
        self.root.rowconfigure(1, weight = 10)
        self.root.columnconfigure(0, weight = 1, minsize = 400)
        self.root.columnconfigure(1, weight = 1, minsize = 400)
        self.root.columnconfigure(2, weight = 1, minsize = 400)

        self.header = tk.Frame(self.root, relief = tk.RAISED, bd = 2)
        self.right_col = tk.Frame(self.root, relief = tk.RAISED, bd=2)
        self.mid_col = tk.Frame(self.root, relief = tk.RAISED, bd=2)
        self.left_col = tk.Frame(self.root, relief = tk.RAISED, bd=2)

        self.header.grid(row = 0, column = 0, columnspan = 3, sticky = "nsew")
        self.right_col.grid(row = 1, column = 0, sticky = "nsew")
        self.mid_col.grid(row = 1, column = 1, sticky = "nsew")
        self.left_col.grid(row = 1, column = 2, sticky = "nsew")

        #set header
        tk.Button(self.header, text = "Reference folder :",
                  command = lambda: self.open_progress_bar("reference",self.get_reference)).grid(row = 0, column = 0,
                                                                                                 sticky = "ew", padx = 5, pady = 5)
        self.reference_folder_entry = tk.Entry(self.header,
                                               bg = "white", fg = "black", width = 200)
        self.reference_folder_entry.grid(row = 0, column = 1, columnspan = 2,
                                         sticky = "ew", padx = 5, pady = 5)

        tk.Button(self.header, text = "Measurements folder :",
                  command = lambda: self.open_progress_bar("measurements",self.get_measurements)).grid(row = 1, column = 0,
                                                                                                  sticky = "ew", padx = 5, pady = 5)
        self.meas_folder_entry = tk.Entry(self.header,
                                               bg = "white", fg = "black", width = 200)
        self.meas_folder_entry.grid(row = 1, column = 1, columnspan = 2,
                                         sticky = "ew", padx = 5, pady = 5)

        #set right-column/monochromatic image
        #change retunrs fo get measurements angles and add leds list
        

    def get_reference(self, progress_window, callback):
        self.reference, self.flatfield_shape, folder_path = read_reference(0.7)
        if folder_path:
            self.reference_folder_entry.delete(0, tk.END)
            self.reference_folder_entry.insert(0, folder_path)

        progress_window.after(0, callback)

        print(f"Reference read from {folder_path}")

    def get_measurements(self,progress_window,callback):
        self.hyperpi_data, folder_path = read_hyperpi_data(self.reference,self.flatfield_shape)
        if folder_path:
            self.meas_folder_entry.delete(0, tk.END)
            self.meas_folder_entry.insert(0, folder_path)

        progress_window.after(0, callback)

        print(f"Measurements read from {folder_path}")

    def open_progress_bar(self,process,function):
        progress_window = tk.Toplevel(self.root)
        progress_window.title(f"Reading {process}...")

        tk.Label(progress_window,
                 text=f"After selecting {process} folder, the reading will start.").pack(pady = 10)
    
        progress_bar = ttk.Progressbar(progress_window, orient="horizontal",
                                       length=300, mode="indeterminate")
        progress_bar.pack(pady=10)

        tk.Label(progress_window,
                 text="Please, wait for this window to close.").pack(pady = 10)
            
        progress_bar.start()
        def close_progress_window():
            progress_bar.stop()
            progress_window.destroy()

        threading.Thread(target = function, args = (progress_window,close_progress_window)).start()


try:
    window = tk.Tk()

    app = Data_analysis(window)
    window.mainloop()
finally:
    print("Bye")
