import numpy as np
from tkinter import filedialog
import tkinter as tk
from tkinter import ttk
import threading
import time
import os
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from data_analysis_functions import *

LEDs = [445, 490, 520, 560, 580, 600, 620, 660, 680, 730, 800, 850, 880, 940, 980]

class Monochromatic_image:
    def __init__(self,root,data,leds,angles):
        self.root = root
        self.data = data
        self.leds = leds
        self.angles = angles
        self.root.title("Monochromatic image")

        #define canvas
        self.fig, self.ax = plt.subplots(figsize = (7,6), ncols=1)
        self.canvas = FigureCanvasTkAgg(self.fig, master = self.root)
        self.canvas.draw()
        self.canvas.get_tk_widget().grid(row = 0, column = 0, columnspan = 3)

        #menubutton for leds
        self.current_led = tk.IntVar(value = self.leds[0])
        self.mbtn_leds = tk.Menubutton(self.root, text = "Select LED", relief = tk.RAISED)
        self.mbtn_leds.grid()
        self.mbtn_leds.menu = tk.Menu(self.mbtn_leds, tearoff = 0)
        self.mbtn_leds["menu"] = self.mbtn_leds.menu

        for led in self.leds:
            self.mbtn_leds.menu.add_radiobutton(label = str(led), variable = self.current_led, value = led)

        self.mbtn_leds.grid(row = 1, column = 0, sticky = "nsew")
        self.current_led.trace_add("write", lambda *args: self.update_image())
        #menubutton for angles
        self.current_angle = tk.DoubleVar(value = self.angles[0])
        self.mbtn_angles = tk.Menubutton(self.root, text = "Select angle", relief = tk.RAISED)
        self.mbtn_angles.grid()
        self.mbtn_angles.menu = tk.Menu(self.mbtn_angles, tearoff = 0)
        self.mbtn_angles["menu"] = self.mbtn_angles.menu

        for angle in self.angles:
            self.mbtn_angles.menu.add_radiobutton(label = str(angle), variable = self.current_angle, value = angle)

        self.mbtn_angles.grid(row = 1, column = 1, sticky = "nsew")
        self.current_angle.trace_add("write", lambda *args: self.update_image())

        #save image
        tk.Button(self.root, text = "Save image",
                  command = self.save_image).grid(row = 1, column = 2,sticky = "ew", padx = 5, pady = 5)

        #make mask
        tk.Button(self.root, text = "Make mask",
                  command = self.monochromatic_mask).grid(row = 2, column = 0,sticky = "ew", padx = 5, pady = 5)

        #show mask
        self.show_mask_btn = tk.Button(self.root, text  =  "Show mask", command = self.show_monochromatic_mask, state = tk.DISABLED)
        self.show_mask_btn.grid(row = 2, column = 1, sticky = "ew", padx = 5, pady = 5)

        #make spectrum image
        self.make_spectra_btn = tk.Button(self.root, text  =  "Get spectrum", command = self.get_spectra_image, state = tk.DISABLED)
        self.make_spectra_btn.grid(row = 3, column = 0, sticky = "ew", padx = 5, pady = 5)

        #make polar image
        self.make_polar_btn = tk.Button(self.root, text  =  "Get intensities", command = self.get_polar_image)
        self.make_polar_btn.grid(row = 3, column = 1, sticky = "ew", padx = 5, pady = 5)

        #close button
        tk.Button(self.root, text = "Close window",
                  command = self.root.destroy).grid(row = 3, column = 2,sticky = "ew", padx = 5, pady = 5)

        self.update_image()

    def update_image(self):
        led = int(self.current_led.get())
        sample = float(self.current_angle.get())
        led_in = self.leds.index(led)
        sample_in = self.angles.index(sample)
        im_xy = self.data[:,:,led_in,sample_in,0]
        im_xy = np.maximum(im_xy,0)
        im_for_visualization = np.sqrt(im_xy)
        
        try:
            self.colorbar.remove()
        except:
            pass
        
        self.ax.clear()
        self.img = self.ax.imshow(im_for_visualization, cmap='gray')
        self.colorbar = self.fig.colorbar(self.img, ax = self.ax, location = "right", shrink = 0.7)
        self.ax.set_xlabel('x (pixel)')
        self.ax.set_ylabel('y (pixel)')
        self.ax.set_title(f"Wavelength : {led}     Angle : {sample}")
        self.canvas.draw()

    def save_image(self):
        folder_path = filedialog.askdirectory(title = "Select save folder.")
        if folder_path:
            file_path = os.path.join(folder_path, f"Monochromatic_image_{self.current_led.get()}nm_{self.current_angle.get()}d.png")
            self.fig.savefig(file_path, bbox_inches = 'tight')
            print("Image saved at:",file_path,sep='\n')
        
    def monochromatic_mask(self):
        led = int(self.current_led.get())
        sample = float(self.current_angle.get())
        led_in = self.leds.index(led)
        sample_in = self.angles.index(sample)

        self.in_mask = make_mask(self.data[:,:,led_in,sample_in,0])
        self.show_mask_btn['state'] = tk.NORMAL
        self.make_spectra_btn['state'] = tk.NORMAL

    def show_monochromatic_mask(self):
        self.in_mask.print_masked_image()
        self.show_mask_btn['state'] = tk.DISABLED
        self.make_spectra_btn['state'] = tk.DISABLED

    def get_spectra_image(self):
        sample = float(self.current_angle.get())
        sample_in = self.angles.index(sample)
        new_window = tk.Toplevel(self.root)
        spectra_window = spectrum(new_window, self.data[:,:,:,sample_in,0], self.in_mask.mask, self.leds, sample)

    def get_polar_image(self):
        led = int(self.current_led.get())
        led_in = self.leds.index(led)
        new_window = tk.Toplevel(self.root)
        polar_window = polar_intensities(new_window, self.data[:,:,led_in,:,:], self.angles, led)

class polar_intensities:
    def __init__(self,root,data,angles,led):
        self.root = root
        self.data = data
        self.angles = angles
        self.led = led

        self.root.title(f"Intensity of {self.led}nm LED")

        self.data_copol = np.mean(data[:,:,:,0], axis=(0, 1))
        self.data_depol = np.mean(data[:,:,:,1], axis=(0, 1))

        #define canvas
        self.fig, self.ax = plt.subplots(figsize = (5,5), subplot_kw={'projection': 'polar'})
        self.canvas = FigureCanvasTkAgg(self.fig, master = self.root)
        self.canvas.draw()
        self.canvas.get_tk_widget().grid(row = 0, column = 0, columnspan = 3)
        
        self.ax.plot(np.radians(self.angles), self.data_copol, 'b.-', markersize=12, label='Copolarized')
        self.ax.plot(np.radians(self.angles), self.data_depol, 'r.-', markersize=12, label='Depolarized')
        self.ax.legend(loc = 'upper right')
        self.ax.set_rlabel_position(-22.5)  # Ajustar la posición del label radial si es necesario
        self.ax.set_xlabel('Degrees (°)')
        self.ax.set_ylabel('Intensity')
        self.ax.set_thetamin(self.angles[0] - 10.0)
        self.ax.set_thetamax(self.angles[-1] + 10.0)
        self.ax.grid(True)

        tk.Button(self.root, text = "Save image",
                  command = self.save_image).grid(row = 1, column = 0,sticky = "ew", padx = 5, pady = 5)
        tk.Button(self.root, text = "Print intensities",
                  command = self.print_spectrum).grid(row = 1, column = 1,sticky = "ew", padx = 5, pady = 5)
        tk.Button(self.root, text = "Close window",
                  command = self.root.destroy).grid(row = 1, column = 2,sticky = "ew", padx = 5, pady = 5)

    def save_image(self):
        folder_path = filedialog.askdirectory(title = "Select save folder.")
        if folder_path:
            file_path = os.path.join(folder_path, f"Intensities_{self.led}nm.png")
            self.fig.savefig(file_path, bbox_inches = 'tight')
            print("Image saved at:",file_path,sep='\n')

    def print_spectrum(self):
        print("\n","-"*10,"Intensities","-"*10,sep = "")
        print("Angle [°] \t Copol Intensity \t Depol Intensity")
        for i in range(len(self.angles)):
            print(self.angles[i],"\t"*2,self.data_copol[i],"\t"*2,self.data_depol[i])
        
        
class spectrum:
    def __init__(self, root, data, mask, leds, angle):
        self.root = root
        self.data = data
        self.mask = mask
        self.leds = leds
        self.angle = angle

        self.root.title(f"Spectrum reflectance at {self.angle}° (copolarized)")

        mask_expanded = np.stack([self.mask] * len(self.leds), axis=-1)
        spectrum_matrix = self.data*mask_expanded
        spectrum = np.sum(spectrum_matrix, axis=(0, 1)) / np.sum(self.mask)
        self.spectrum = spectrum*100
        
        #define canvas
        self.fig, self.ax = plt.subplots(figsize = (6,5), ncols=1)
        self.canvas = FigureCanvasTkAgg(self.fig, master = self.root)
        self.canvas.draw()
        self.canvas.get_tk_widget().grid(row = 0, column = 0, columnspan = 3)
        self.ax.plot(self.leds, self.spectrum, 'k.-', markersize=12)
        self.ax.set_xlabel('Wavelength [nm]')
        self.ax.set_ylabel('Reflectance [%]')
        self.ax.set_xlim(300, 1020)
        self.ax.set_xticks(np.arange(300, 1020, 100))
        self.ax.grid()

        tk.Button(self.root, text = "Save image",
                  command = self.save_image).grid(row = 1, column = 0,sticky = "ew", padx = 5, pady = 5)
        tk.Button(self.root, text = "Print spectrum",
                  command = self.print_spectrum).grid(row = 1, column = 1,sticky = "ew", padx = 5, pady = 5)
        tk.Button(self.root, text = "Close window",
                  command = self.root.destroy).grid(row = 1, column = 2,sticky = "ew", padx = 5, pady = 5)

    def save_image(self):
        folder_path = filedialog.askdirectory(title = "Select save folder.")
        if folder_path:
            file_path = os.path.join(folder_path, f"Spectrum_{self.angle}d.png")
            self.fig.savefig(file_path, bbox_inches = 'tight')
            print("Image saved at:",file_path,sep='\n')

    def print_spectrum(self):
        print("\n","-"*10,"Spectrum","-"*10,sep = "")
        print("Wavelength [nm] \t Reflectence [%]")
        for i in range(len(self.leds)):
            print(self.leds[i],"\t"*3,self.spectrum[i])

class FalseColorImage:
    def __init__(self,root,data,leds,angles):
        self.root = root
        self.data = data
        self.leds = leds
        self.sampler_angles = angles

        self.root.title("False color image (copolarized)")
        
        #define canvas
        self.fig, self.ax = plt.subplots(figsize = (7,6), ncols=1)
        self.canvas = FigureCanvasTkAgg(self.fig, master = self.root)
        self.canvas.draw()
        self.canvas.get_tk_widget().grid(row = 0, column = 0, columnspan = 3)

        #menubutton for leds R
        self.led_r = tk.IntVar(value = self.leds[8])
        self.mbtn_leds_r = tk.Menubutton(self.root, text = "Select R-LED", relief = tk.RAISED)
        self.mbtn_leds_r.grid()
        self.mbtn_leds_r.menu = tk.Menu(self.mbtn_leds_r, tearoff = 0)
        self.mbtn_leds_r["menu"] = self.mbtn_leds_r.menu

        for led in self.leds:
            self.mbtn_leds_r.menu.add_radiobutton(label = str(led), variable = self.led_r, value = led)

        self.mbtn_leds_r.grid(row = 1, column = 0, sticky = "nsew")
        self.led_r.trace_add("write", lambda *args: self.update_image())

        #menubutton for leds G
        self.led_g = tk.IntVar(value = self.leds[3])
        self.mbtn_leds_g = tk.Menubutton(self.root, text = "Select G-LED", relief = tk.RAISED)
        self.mbtn_leds_g.grid()
        self.mbtn_leds_g.menu = tk.Menu(self.mbtn_leds_g, tearoff = 0)
        self.mbtn_leds_g["menu"] = self.mbtn_leds_g.menu

        for led in self.leds:
            self.mbtn_leds_g.menu.add_radiobutton(label = str(led), variable = self.led_g, value = led)

        self.mbtn_leds_g.grid(row = 1, column = 1, sticky = "nsew")
        self.led_g.trace_add("write", lambda *args: self.update_image())

        #menubutton for leds B
        self.led_b = tk.IntVar(value = self.leds[0])
        self.mbtn_leds_b = tk.Menubutton(self.root, text = "Select B-LED", relief = tk.RAISED)
        self.mbtn_leds_b.grid()
        self.mbtn_leds_b.menu = tk.Menu(self.mbtn_leds_b, tearoff = 0)
        self.mbtn_leds_b["menu"] = self.mbtn_leds_b.menu

        for led in self.leds:
            self.mbtn_leds_b.menu.add_radiobutton(label = str(led), variable = self.led_b, value = led)

        self.mbtn_leds_b.grid(row = 1, column = 2, sticky = "nsew")
        self.led_b.trace_add("write", lambda *args: self.update_image())
        
        #menubutton for angles
        self.current_angle = tk.DoubleVar(value = self.sampler_angles[0])
        self.mbtn_angles = tk.Menubutton(self.root, text = "Select angle", relief = tk.RAISED)
        self.mbtn_angles.grid()
        self.mbtn_angles.menu = tk.Menu(self.mbtn_angles, tearoff = 0)
        self.mbtn_angles["menu"] = self.mbtn_angles.menu

        for angle in self.sampler_angles:
            self.mbtn_angles.menu.add_radiobutton(label = str(angle), variable = self.current_angle, value = angle)

        self.mbtn_angles.grid(row = 2, column = 0, sticky = "nsew")
        self.current_angle.trace_add("write", lambda *args: self.update_image())

        #button for entry
        tk.Button(self.root, text = "Set Gain",
                  command = self.update_image).grid(row = 2, column = 1, sticky = "ew", padx = 5, pady = 5)
        
        #gain entry
        self.gain = tk.Entry(self.root, bg = "white", fg = "black", width = 12)
        self.gain.grid(row = 2, column = 2, sticky = "nsew")
        self.gain.insert(0,"1.0")

        #save image
        tk.Button(self.root, text = "Save image",
                  command = self.save_image).grid(row = 3, column = 0, sticky = "ew", padx = 5, pady = 5)

        #close button
        tk.Button(self.root, text = "Close window",
                  command = self.root.destroy).grid(row = 3, column = 2,sticky = "ew", padx = 5, pady = 5)

        self.update_image()

    def update_image(self):
        r_in = self.leds.index(self.led_r.get())
        g_in = self.leds.index(self.led_g.get())
        b_in = self.leds.index(self.led_b.get())
        angle_in = self.sampler_angles.index(self.current_angle.get())
        gain = float(self.gain.get())
        
        false_color_im = np.stack([self.data[:,:,r_in,angle_in,0],
                                  self.data[:,:,g_in,angle_in,0],
                                  self.data[:,:,b_in,angle_in,0]],
                                  axis=-1)

        false_color_im = np.maximum(false_color_im, 0)
        false_color_im = gain*np.sqrt(false_color_im)
        self.ax.clear()
        self.img = self.ax.imshow(false_color_im, cmap='nipy_spectral')
        self.ax.set_xlabel('x (pixel)')
        self.ax.set_ylabel('y (pixel)')
        self.ax.set_title(f"R({self.leds[r_in]}nm)    G({self.leds[g_in]}nm)    B({self.leds[b_in]}nm)")
        self.canvas.draw()

    def save_image(self):
        folder_path = filedialog.askdirectory(title = "Select save folder.")
        if folder_path:
            file_path = os.path.join(folder_path, f"FC_image_R-{self.led_r.get()}nm_G-{self.led_g.get()}nm_B-{self.led_b.get()}nm_{self.current_angle.get()}d.png")
            self.fig.savefig(file_path, bbox_inches = 'tight')
            print("Image saved at:",file_path,sep='\n')

class ElipsoImage:
    def __init__(self,root,data,leds,angles):
        self.root = root
        self.data = data
        self.leds = leds
        self.sampler_angles = angles

        self.root.title("Copolarized-Depolarized image")
        
        #define canvas
        self.fig, self.ax = plt.subplots(figsize = (7,6), ncols=1)
        self.canvas = FigureCanvasTkAgg(self.fig, master = self.root)
        self.canvas.draw()
        self.canvas.get_tk_widget().grid(row = 0, column = 0, columnspan = 3)

        #menubutton for leds R
        self.current_led = tk.IntVar(value = self.leds[0])
        self.mbtn_leds = tk.Menubutton(self.root, text = "Select LED", relief = tk.RAISED)
        self.mbtn_leds.grid()
        self.mbtn_leds.menu = tk.Menu(self.mbtn_leds, tearoff = 0)
        self.mbtn_leds["menu"] = self.mbtn_leds.menu

        for led in self.leds:
            self.mbtn_leds.menu.add_radiobutton(label = str(led), variable = self.current_led, value = led)

        self.mbtn_leds.grid(row = 1, column = 0, sticky = "nsew")
        self.current_led.trace_add("write", lambda *args: self.update_image())

        #menubutton for angles
        self.current_angle = tk.DoubleVar(value = self.sampler_angles[0])
        self.mbtn_angles = tk.Menubutton(self.root, text = "Select angle", relief = tk.RAISED)
        self.mbtn_angles.grid()
        self.mbtn_angles.menu = tk.Menu(self.mbtn_angles, tearoff = 0)
        self.mbtn_angles["menu"] = self.mbtn_angles.menu

        for angle in self.sampler_angles:
            self.mbtn_angles.menu.add_radiobutton(label = str(angle), variable = self.current_angle, value = angle)

        self.mbtn_angles.grid(row = 1, column = 1, sticky = "nsew")
        self.current_angle.trace_add("write", lambda *args: self.update_image())

        #save image
        tk.Button(self.root, text = "Save image",
                  command = self.save_image).grid(row = 1, column = 2, sticky = "ew", padx = 5, pady = 5)

        tk.Label(self.root, text = "Copol-Depol Gain :").grid(row = 2, column = 0, sticky = "ew", padx = 5, pady = 5)
        
        #gain entry
        self.codepol_gain = tk.Entry(self.root, bg = "white", fg = "black", width = 12)
        self.codepol_gain.grid(row = 2, column = 1, sticky = "nsew")
        self.codepol_gain.insert(0,"1.0")

        tk.Button(self.root, text = "Set Gains",
                  command = self.update_image).grid(row = 2, column = 2, sticky = "ew", padx = 5, pady = 5)

        tk.Label(self.root, text = "Depol Gain :").grid(row = 3, column = 0, sticky = "ew", padx = 5, pady = 5)
        
        #gain entry
        self.depol_gain = tk.Entry(self.root, bg = "white", fg = "black", width = 12)
        self.depol_gain.grid(row = 3, column = 1, sticky = "nsew")
        self.depol_gain.insert(0,"1.0")

        tk.Label(self.root, text = "Copol Gain :").grid(row = 4, column = 0, sticky = "ew", padx = 5, pady = 5)
        
        #gain entry
        self.copol_gain = tk.Entry(self.root, bg = "white", fg = "black", width = 12)
        self.copol_gain.grid(row = 4, column = 1, sticky = "nsew")
        self.copol_gain.insert(0,"0.0")

        #close button
        tk.Button(self.root, text = "Close window",
                  command = self.root.destroy).grid(row = 4, column = 2,sticky = "ew", padx = 5, pady = 5)

        self.update_image()

    def update_image(self):
        led_in = self.leds.index(self.current_led.get())
        angle_in = self.sampler_angles.index(self.current_angle.get())
        codepol_gain = float(self.codepol_gain.get())
        copol_gain = float(self.copol_gain.get())
        depol_gain = float(self.depol_gain.get())
        
        pol_falsecolor = np.stack([depol_gain*self.data[:,:,led_in,angle_in,1],
                                   codepol_gain*(self.data[:,:,led_in,angle_in,0] - self.data[:,:,led_in,angle_in,1]),
                                   copol_gain*self.data[:,:,led_in,angle_in,0]], axis=-1)
        
        pol_falsecolor = np.clip(pol_falsecolor, 0, 1)
        
        self.ax.clear()
        self.img = self.ax.imshow(pol_falsecolor)
        self.ax.set_xlabel('x (pixel)')
        self.ax.set_ylabel('y (pixel)')
        self.ax.set_title(f"R : depol    G : copol - depol")
        self.canvas.draw()

    def save_image(self):
        folder_path = filedialog.askdirectory(title = "Select save folder.")
        if folder_path:
            file_path = os.path.join(folder_path, f"Copol-Depol_image_{self.current_led.get()}nm_{self.current_angle.get()}d.png")
            self.fig.savefig(file_path, bbox_inches = 'tight')
            print("Image saved at:",file_path,sep='\n')
        

class Data_analysis:
    def __init__(self, root, leds):
        self.root = root
        self.reference = None
        self.flatfield_shape = None
        self.hyperpi_data = None
        self.leds = leds
        self.sample_angles = None
        self.root.title("Data analysis console for HyperPi project")

        #set GUI frames
        self.root.rowconfigure(0, weight = 1)
        self.root.rowconfigure(1, weight = 1)
        self.root.columnconfigure(0, weight = 1, minsize = 250)
        self.root.columnconfigure(1, weight = 1, minsize = 250)
        self.root.columnconfigure(2, weight = 1, minsize = 250)

        self.header = tk.Frame(self.root, relief = tk.RAISED, bd = 2)
        self.right_col = tk.Frame(self.root, relief = tk.RAISED, bd=2)
        self.mid_col = tk.Frame(self.root, relief = tk.RAISED, bd=2)
        self.left_col = tk.Frame(self.root, relief = tk.RAISED, bd=2)

        self.header.grid(row = 0, column = 0, columnspan = 3, sticky = "nsew")
        self.right_col.grid(row = 1, column = 2, sticky = "nsew")
        self.mid_col.grid(row = 1, column = 1, sticky = "nsew")
        self.left_col.grid(row = 1, column = 0, sticky = "nsew")

        #set header
        tk.Button(self.header, text = "Reference folder :",
                  command = lambda: self.open_progress_bar("reference",self.get_reference)).grid(row = 0, column = 0,
                                                                                                 sticky = "ew", padx = 5, pady = 5)
        self.reference_folder_entry = tk.Entry(self.header,
                                               bg = "white", fg = "black", width = 100)
        self.reference_folder_entry.grid(row = 0, column = 1, columnspan = 2,
                                         sticky = "ew", padx = 5, pady = 5)

        tk.Button(self.header, text = "Measurements folder :",
                  command = lambda: self.open_progress_bar("measurements",self.get_measurements)).grid(row = 1, column = 0,
                                                                                                  sticky = "ew", padx = 5, pady = 5)
        self.meas_folder_entry = tk.Entry(self.header,
                                               bg = "white", fg = "black", width = 100)
        self.meas_folder_entry.grid(row = 1, column = 1, columnspan = 2,
                                         sticky = "ew", padx = 5, pady = 5)

        #set left-column/monochromatic image
        tk.Button(self.left_col, text = "Generate Monochromatic Image",
                  command = self.gen_monochromatic).pack()#.grid(row = 0, column = 0, sticky = "ns", padx = 5, pady = 5)

        #set mid-column/false color image
        tk.Button(self.mid_col, text = "Generate False Color Image",
                  command = self.gen_false_color_image).pack()#.grid(row = 0, column = 0,sticky = "ns", padx = 5, pady = 5)

        #set right-column/false color image
        tk.Button(self.right_col, text = "Generate Copol-Depol Image",
                  command = self.gen_elipso_image).pack()#.grid(row = 0, column = 0,sticky = "ns", padx = 5, pady = 5)
        

    def get_reference(self, progress_window, callback):
        self.reference, self.flatfield_shape, folder_path = read_reference(0.7)
        if folder_path:
            self.reference_folder_entry.delete(0, tk.END)
            self.reference_folder_entry.insert(0, folder_path)

        progress_window.after(0, callback)

        print(f"Reference read from {folder_path}")

    def get_measurements(self,progress_window,callback):
        self.hyperpi_data, folder_path, angles = read_hyperpi_data(self.reference,self.flatfield_shape)
        if folder_path:
            self.meas_folder_entry.delete(0, tk.END)
            self.meas_folder_entry.insert(0, folder_path)

        self.sample_angles = [float(txt.strip().split("_")[-1]) for txt in angles]

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

    def gen_monochromatic(self):
        new_window = tk.Toplevel(self.root)
        new_mono = Monochromatic_image(new_window,self.hyperpi_data,self.leds,self.sample_angles)

    def gen_false_color_image(self):
        new_window = tk.Toplevel(self.root)
        new_fci = FalseColorImage(new_window,self.hyperpi_data,self.leds,self.sample_angles)

    def gen_elipso_image(self):
        new_window = tk.Toplevel(self.root)
        new_elipso = ElipsoImage(new_window,self.hyperpi_data,self.leds,self.sample_angles)

try:
    window = tk.Tk()

    app = Data_analysis(window, LEDs)
    window.mainloop()
finally:
    try:
        window.destroy()
    except:
        pass
    print("Bye")
