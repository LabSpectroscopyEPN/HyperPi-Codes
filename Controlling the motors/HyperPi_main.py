import numpy as np
import pandas as pd
from skimage.io import imread

def read_biospace_reference(folder_name, reference_reflectance, pol=0):
    # Load constants
    lambda_LEDs, resolution = load_constants()
    
    # Initialize variables
    exp_time, gain, _ = read_nodefile(folder_name)
    linear_gain = 10 ** (gain / 10)

    # Read the protocol file and save info on what angles were used
    protocol = pd.read_csv(f'{folder_name}/protocol.csv', header=None).values
    yaw_angles = np.unique(protocol[:, 1])
    
    led_intensities = np.zeros((len(lambda_LEDs), len(yaw_angles)))
    homogeneity = None  # To be defined later based on image size

    for yaw in range(len(yaw_angles)):
        background = imread(f'{folder_name}/scatter_0_yaw_{yaw_angles[yaw]}_roll_0/background.tiff')

        for lambda_ind in range(len(lambda_LEDs)):
            fn = f'{folder_name}/scatter_0_yaw_{yaw_angles[yaw]}_roll_0/{lambda_LEDs[lambda_ind]}nm.tiff'
            im = imread(fn)
            im = im - background

            if homogeneity is None:
                homogeneity = np.zeros((*im.shape, len(lambda_LEDs), len(yaw_angles)))

            im_hat = regression_2d_3rd_order(im)
            led_intensities[lambda_ind, yaw] = np.mean(im) / (exp_time * linear_gain * reference_reflectance)
            homogeneity[:, :, lambda_ind, yaw] = im_hat / (exp_time * linear_gain * reference_reflectance)

    homogeneity = np.mean(homogeneity, axis=(2, 3))
    homogeneity = homogeneity / np.mean(homogeneity)
    led_intensities = np.mean(led_intensities, axis=1)
    
    return led_intensities, homogeneity

def load_constants():
    lambda_LEDs = np.array([365, 405, 430, 490, 525, 630, 810, 940])  # [nm]
    resolution = 0.0334  # [mm] for 1 pixel (3x3 binning)
    return lambda_LEDs, resolution

def read_nodefile(folder_name):
    # Dummy implementation, replace with actual file reading logic
    exp_time = 1.0
    gain = 2.0
    binning = 3
    return exp_time, gain, binning

def regression_2d_3rd_order(im):
    # Dummy implementation, replace with actual regression logic
    return im  # Assuming no change for the placeholder

# Dummy value for resolution, replace with actual value if needed
resolution = 1.0
