import numpy as np
import cv2  # OpenCV para cargar imágenes
import os
import pandas as pd

# --- Constants (from load_constants.m) ---
lambda_LEDs = np.array([365, 405, 430, 490, 525, 630, 810, 940])  # [nm]
resolution = 0.0334  # [mm] for 1 pixel (3x3 binning)

# --- Functions ---
def regression_2d_3rd_order(im):
    """
    Returns a regressed image based on a third-order polynomial in two dimensions.
    """
    x, y = np.meshgrid(np.linspace(-1, 1, im.shape[1]), np.linspace(-1, 1, im.shape[0]))
    
    regr = np.column_stack([
        np.ones(x.size),  # x^0
        x.ravel(),        # x^1
        x.ravel()**2,     # x^2
        x.ravel()**3,     # x^3
        y.ravel(),        # y^1
        y.ravel()**2,     # y^2
        y.ravel()**3,     # y^3
        x.ravel() * y.ravel(),           # x^1 * y^1
        x.ravel() * y.ravel()**2,        # x^1 * y^2
        x.ravel()**2 * y.ravel()         # x^2 * y^1
    ])
    
    coef, _, _, _ = np.linalg.lstsq(regr, im.ravel(), rcond=None)
    im_hat = regr.dot(coef)
    im_hat = im_hat.reshape(im.shape)
    
    return im_hat

def read_nodefile(folder_name):
    """
    Returns exp_time, gain and binning used by a Basler camera.
    """
    nodefile_name = [f for f in os.listdir(folder_name) if f.endswith('.pfs')][0]
    nodefile = pd.read_csv(os.path.join(folder_name, nodefile_name), sep='\t', skiprows=3, header=None)
    
    exp_time = float(nodefile.loc[nodefile[0] == 'ExposureTime', 1].values[0]) / 1000
    gain = float(nodefile.loc[nodefile[0] == 'Gain', 1].values[0])
    binning = int(nodefile.loc[nodefile[0] == 'BinningHorizontal', 1].values[0])
    
    return exp_time, gain, binning

def read_biospace_reference(folder_name, reference_reflectance, pol=0):
    """
    Returns the led_intensities for BIOSPACE and the homogeneity.
    """
    if pol:
        subFolderName = '\\scatter_0_yaw_0_roll_0_polarization_0\\'
    else:
        subFolderName = '\\scatter_0_yaw_0_roll_'
    
    exp_time, gain, _ = read_nodefile(folder_name)
    linear_gain = 10 ** (gain / 10)
    
    protocol = pd.read_csv(os.path.join(folder_name, 'protocol.csv'), header=None).values
    yaw_angles = np.unique(protocol[:, 1])
    
    led_intensities = np.zeros((len(lambda_LEDs), len(yaw_angles)))
    homogeneity = np.zeros((None, None, len(lambda_LEDs), len(yaw_angles)))
    
    for yaw in range(len(yaw_angles)):
        background = cv2.imread(os.path.join(folder_name, f'scatter_0_yaw_{int(yaw_angles[yaw])}_roll_0', 'background.tiff'), cv2.IMREAD_UNCHANGED)
        
        for lambda_ind in range(len(lambda_LEDs)):
            fn = os.path.join(folder_name, f'scatter_0_yaw_{int(yaw_angles[yaw])}_roll_0', f'{lambda_LEDs[lambda_ind]}nm.tiff')
            im = cv2.imread(fn, cv2.IMREAD_UNCHANGED)
            im = im - background
            
            im_hat = regression_2d_3rd_order(im)
            led_intensities[lambda_ind, yaw] = np.mean(im) / (exp_time * linear_gain * reference_reflectance)
            homogeneity[:, :, lambda_ind, yaw] = im_hat / (exp_time * linear_gain * reference_reflectance)
    
    homogeneity = np.mean(homogeneity, axis=(2, 3))
    homogeneity = homogeneity / np.mean(homogeneity)
    led_intensities = np.mean(led_intensities, axis=1)
    
    return led_intensities, homogeneity
