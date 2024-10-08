import numpy as np
import pandas as pd
import tkinter as tk
import os
from tkinter import filedialog
from skimage.io import imread as sk_imageread
import matplotlib.pyplot as plt
from matplotlib.widgets import PolygonSelector
from matplotlib.image import AxesImage
from PIL import Image, ImageDraw
import cv2

def regression_2d_3rd_order(im):
    if  len(im.shape) == 3:
        im = np.mean(im, axis=2)

    x, y = np.meshgrid(np.linspace(-1, 1, im.shape[1]), np.linspace(-1, 1, im.shape[0]))
    regr = np.column_stack([
        x.flatten()**0, x.flatten(), x.flatten()**2, x.flatten()**3,
        y.flatten(), y.flatten()**2, y.flatten()**3,
        x.flatten() * y.flatten(), x.flatten() * y.flatten()**2,
        x.flatten()**2 * y.flatten()
    ])
    coef = np.linalg.lstsq(regr, im.flatten(), rcond=None)[0]
    im_hat = regr @ coef
    return im_hat.reshape(im.shape)

def read_controls_file(folder_path):
    data_dict = {}
    data_type = {"Int":int,
                 "Float":float,
                "String":str,
                "List":eval,
                "Tuple":eval}
    #folder_path = filedialog.askdirectory(title = "Select the controls measurements")
        
    for file in os.listdir(folder_path):
        if file.endswith(".txt"):
            file_path = os.path.join(folder_path, file)
            try:
                with open(file_path, 'r') as file:
                    for line in file:
                        columns = line.strip().split()
                        if len(columns) == 3:
                            key, value, type_var = columns
                            data_dict[key] = data_type[type_var](value)
                return data_dict
            except FileNotFoundError:
                print(f"File '{file}' not found at {folder_path}")
                return {}
            except Exception as e:
                print(f"Error: {str(e)}")
    print(f"Error: No .txt file found at {folder_path}")
    return {}

def read_reference(reference_reflectance,extension=".tiff"):
    
    folder_path = filedialog.askdirectory(title = "Select the reference measurements")
    controls = read_controls_file(folder_path)
    copol_folders = [folder for folder in os.listdir(folder_path) if folder.startswith("Copol_Sampler_")]
    linear_gain = 10**(controls["AnalogueGain"]/10)
    LEDs = [445, 490, 520, 560, 580, 600, 620, 660, 680, 730, 800, 850, 880, 940, 980]
    led_intensities = np.zeros(len(LEDs))
    homogeneity = None

    for copol_folder in copol_folders:
        background_path = os.path.join(folder_path, copol_folder, "background" + extension)
        background = sk_imageread(background_path)

        if homogeneity is None:
            homogeneity = np.zeros([background.shape[0], background.shape[1],
                                    len(LEDs), len(copol_folders)])

        for wavelength in LEDs:
            fn = os.path.join(folder_path, copol_folder, f"{wavelength}" + extension)
            im = sk_imageread(fn) - background

            im_hat = regression_2d_3rd_order(im)
            led_intensities[LEDs.index(wavelength)] += np.mean(im) / (controls["ExposureTime"] * linear_gain * reference_reflectance)
            homogeneity[:, :, LEDs.index(wavelength), copol_folders.index(copol_folder)] = im_hat / (controls["ExposureTime"] * linear_gain * reference_reflectance)

    led_intensities = np.mean(led_intensities)

    if homogeneity.ndim == 4:
        homogeneity = np.mean(homogeneity, axis=(2, 3))
    else:
        homogeneity = np.mean(homogeneity, axis=tuple(range(homogeneity.ndim)))

    homogeneity = homogeneity / np.mean(homogeneity)
    return led_intensities, homogeneity, folder_path


def read_hyperpi_data(reference, flatfield_shape, extension=".tiff"):

    folder_path = filedialog.askdirectory(title = "Select the measurements to analize")
    controls = read_controls_file(folder_path)
    LEDs = [445, 490, 520, 560, 580, 600, 620, 660, 680, 730, 800, 850, 880, 940, 980]
    copol_folders = [folder for folder in os.listdir(folder_path) if folder.startswith("Copol_Sampler_")]
    depol_folders = [folder for folder in os.listdir(folder_path) if folder.startswith("Depol_Sampler_")]
    polarization_angles = [0,90]
    assert len(copol_folders) == len(depol_folders), "Non equal number of Copol-Depol folders.\n Check Measurements folder or read_hyperpi_data function."
    dividend = controls["ExposureTime"] * (10 ** (controls["AnalogueGain"] / 10)) * reference

    data_shape = (controls["Height"], controls["Width"], len(LEDs), len(copol_folders), len(polarization_angles))
    
    hyperpi_data = np.zeros(data_shape, dtype=np.float32)

    def to_data(in_folder, wavelength, in_wave, in_sample, in_pol):
        image_path = os.path.join(folder_path, in_folder, f"{wavelength}" + extension)
        image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        assert image.any() != None, f"Error while loading {image_path}"

        background_path = os.path.join(folder_path,in_folder,"background" + extension)
        background = cv2.imread(background_path, cv2.IMREAD_GRAYSCALE)
        assert background.any() != None, f"Error while loading {background_path}"

        data = image - background
        data = data * flatfield_shape
        assert data.shape == hyperpi_data[:,:,in_wave,in_sample,in_pol].shape, "Shape mismatch"
        
        return data

    if polarization_angles == [0,90]:
        for (sample,(copol_folder, depol_folder)) in enumerate(zip(copol_folders,depol_folders)):
            for wave_index, wavelength in enumerate(LEDs):
                hyperpi_data[:,:,wave_index,sample,0] = to_data(copol_folder, wavelength, wave_index, sample, 0) / dividend
                hyperpi_data[:,:,wave_index,sample,1] = to_data(depol_folder, wavelength, wave_index, sample, 1) / dividend

    return hyperpi_data, folder_path, copol_folders

class make_mask:
    def __init__(self,original_image):
        self.original_image = original_image
        
        self.fig_org, self.ax_org = plt.subplots()
        self.fig_mask, self.ax_mask = plt.subplots()
        
        self.new_image = np.empty(np.shape(self.original_image))        
        self.mask = np.zeros(np.shape(self.original_image)[0:2])
        self.depth = 1

        self.ax_org.imshow(self.original_image)
        self.selector =  PolygonSelector(self.ax_org,
                                         onselect = self.do_mask,
                                         draw_bounding_box = True,
                                         props = dict(color = 'r',
                                                      linestyle = '-',
                                                      linewidth = 2)
                                         )
        self.fig_org.show()

    def do_mask(self,vertices):
        plt.close(fig = self.fig_org)
        try:
            height,width,self.depth = np.shape(self.original_image)
        except:
            height,width = np.shape(self.original_image)[0:2]
            self.depth = 1
        img = Image.new('L', (width,height), 0)
        ImageDraw.Draw(img).polygon(vertices, outline=1, fill=1)
        self.mask = np.array(img)
        
    def print_masked_image(self):
        if self.depth == 1:
            new_image = self.original_image * self.mask
            new_image = new_image/np.max(new_image)
        else:
            for i in range(self.depth):
                new_image[:,:,i] = self.original_image[:,:,i] * self.mask
                new_image[:,:,i] = new_image[:,:,i]/np.max(new_image[:,:,i])
        self.ax_mask.imshow(new_image)
        self.fig_mask.show()
