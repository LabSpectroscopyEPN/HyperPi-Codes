from google.colab import drive
drive.mount('/content/drive/')

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
from skimage.io import imread
import imageio
import os
from PIL import Image
import cv2
from pathlib import Path

# Funciones auxiliares traducidas

def regression_2d_3rd_order(im):
    """Returns a regressed image based on third-order polynomial in two dimensions."""
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

def read_nodefile(folder_name):
    """Returns exp_time, gain and binning used by a Basler camera."""
    nodefile_path = os.path.join(folder_name, next(f for f in os.listdir(folder_name) if f.endswith('.pfs')))
    nodefile_data = np.genfromtxt(nodefile_path, delimiter='\t', dtype=str, skip_header=3)

    exp_time = float(nodefile_data[np.where(nodefile_data[:, 0] == 'ExposureTime')[0], 1][0]) / 1000
    gain = float(nodefile_data[np.where(nodefile_data[:, 0] == 'Gain')[0], 1][0])
    binning = int(nodefile_data[np.where(nodefile_data[:, 0] == 'BinningHorizontal')[0], 1][0])

    return exp_time, gain, binning

def read_biospace_reference(folder_name, refernce_reflectance, pol=0):
    """Returns the led_intensities and homogeneity for BIOSPACE."""
    exp_time, gain, _ = read_nodefile(folder_name)
    linear_gain = 10**(gain / 10)

    protocol = np.genfromtxt(os.path.join(folder_name, 'protocol.csv'), delimiter=',')
    yaw_angles = np.unique(protocol[:, 1])

    led_intensities = np.zeros(len(lambda_LEDs))
    homogeneity = None  # Inicia como None para inicializar después

    for yaw in range(len(yaw_angles)):
        background_path = os.path.join(folder_name, f'scatter_0_yaw_{int(yaw_angles[yaw])}_roll_0', 'background.tiff')
        background = imread(background_path)

        # Ahora que background ha sido leído, podemos inicializar homogeneity si es necesario
        if homogeneity is None:
            homogeneity = np.zeros([background.shape[0], background.shape[1], len(lambda_LEDs), len(yaw_angles)])

        for lambda_ind in range(len(lambda_LEDs)):
            fn = os.path.join(folder_name, f'scatter_0_yaw_{int(yaw_angles[yaw])}_roll_0', f'{int(lambda_LEDs[lambda_ind])}nm.tiff')
            im = imread(fn) - background

            im_hat = regression_2d_3rd_order(im)
            led_intensities[lambda_ind] += np.mean(im) / (exp_time * linear_gain * refernce_reflectance)
            homogeneity[:, :, lambda_ind, yaw] = im_hat / (exp_time * linear_gain * refernce_reflectance)

    # Si led_intensities es un array 1D, toma el promedio sin axis
    led_intensities = np.mean(led_intensities)

    # Verifica la dimensionalidad de homogeneity antes de tomar el promedio
    if homogeneity.ndim == 4:
        homogeneity = np.mean(homogeneity, axis=(2, 3))
    else:
        # Si no es 4D, ajusta el axis según las dimensiones actuales
        homogeneity = np.mean(homogeneity, axis=tuple(range(homogeneity.ndim)))

    homogeneity = homogeneity / np.mean(homogeneity)

    return led_intensities, homogeneity

def gif(filename=None, delay_time=1/15, loop_count=float('inf'), frame=None, resolution=None, nodither=False, overwrite=False):
    """Simple function to create GIFs."""
    if filename:
        imageio.mimsave(filename, frame, duration=delay_time, loop=loop_count)

def read_biospace_data(folder_name, reference, flatfield_shape):
    biospace_data = {
        'wavelengths': lambda_LEDs,
        'reference': reference,
        'scatter_angles': [],
        'yaw_angles': [],
        'roll_angles': [],
        'polarization_angles': [],
        'exp_time': None,
        'gain': None,
        'binning': None,
        'resolution': None,
        'linear_gain': None,
        'data': None,
        'x': None,
        'y': None
    }

    # Leer archivo de protocolo y guardar los ángulos utilizados
    protocol = np.loadtxt(os.path.join(folder_name, 'protocol.csv'), delimiter=',')
    biospace_data['scatter_angles'] = np.unique(protocol[:, 0])
    biospace_data['yaw_angles'] = np.unique(protocol[:, 1])
    biospace_data['roll_angles'] = np.unique(protocol[:, 2])

    if protocol.shape[1] == 4:
        biospace_data['polarization_angles'] = np.unique(protocol[:, 3])

    # Encontrar el tiempo de exposición y la ganancia
    biospace_data['exp_time'], biospace_data['gain'], biospace_data['binning'] = read_nodefile(folder_name)
    biospace_data['resolution'] = resolution * biospace_data['binning'] / 3
    biospace_data['linear_gain'] = 10 ** (biospace_data['gain'] / 10)

    # Leer todos los datos y guardarlos en un cubo de datos
    height, width = 400, 640  # Ajustar estos valores según la forma esperada de las imágenes
    polarization_count = len(biospace_data['polarization_angles']) if biospace_data['polarization_angles'] else 1
    data_shape = (
        height,
        width,
        len(lambda_LEDs),
        len(biospace_data['scatter_angles']),
        len(biospace_data['yaw_angles']),
        len(biospace_data['roll_angles']),
        polarization_count
    )
    biospace_data['data'] = np.zeros(data_shape, dtype=np.float32)

    for scatter_ind, scatter in enumerate(biospace_data['scatter_angles']):
        for yaw_ind, yaw in enumerate(biospace_data['yaw_angles']):
            for roll_ind, roll in enumerate(biospace_data['roll_angles']):
                for lambda_ind, wavelength in enumerate(lambda_LEDs):
                    scatter_str = int(scatter)
                    yaw_str = int(yaw)
                    roll_str = int(roll)

                    if biospace_data['polarization_angles']:
                        for pol_ind, pol in enumerate(biospace_data['polarization_angles']):
                            pol_str = int(pol)
                            image_path = os.path.join(
                                folder_name,
                                f'scatter_{scatter_str}_yaw_{yaw_str}_roll_{roll_str}_polarization_{pol_str}',
                                f'{int(wavelength)}nm.tiff'
                            )
                            im_1 = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
                            if im_1 is None:
                                print(f"Error loading image: {image_path}")
                                continue

                            background_path = os.path.join(
                                folder_name,
                                f'scatter_{scatter_str}_yaw_{yaw_str}_roll_{roll_str}_polarization_{pol_str}',
                                'background.tiff'
                            )
                            background = cv2.imread(background_path, cv2.IMREAD_UNCHANGED)
                            if background is None:
                                print(f"Error loading background: {background_path}")
                                continue

                            data = im_1 - background
                            data = data * flatfield_shape
                            # Ajustar el tamaño de data si es necesario
                            if data.shape != biospace_data['data'][:, :, lambda_ind, scatter_ind, yaw_ind, roll_ind, pol_ind].shape:
                                print(f"Shape mismatch: data shape {data.shape}, target shape {biospace_data['data'][:, :, lambda_ind, scatter_ind, yaw_ind, roll_ind, pol_ind].shape}")
                                continue
                            biospace_data['data'][:, :, lambda_ind, scatter_ind, yaw_ind, roll_ind, pol_ind] = data / (
                                    biospace_data['exp_time'] * biospace_data['linear_gain'] * biospace_data['reference']
                            )
                    else:
                        image_path = os.path.join(
                            folder_name,
                            f'scatter_{scatter_str}_yaw_{yaw_str}_roll_{roll_str}',
                            f'{int(wavelength)}nm.tiff'
                        )
                        im_1 = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
                        if im_1 is None:
                            print(f"Error loading image: {image_path}")
                            continue

                        background_path = os.path.join(
                            folder_name,
                            f'scatter_{scatter_str}_yaw_{yaw_str}_roll_{roll_str}',
                            'background.tiff'
                        )
                        background = cv2.imread(background_path, cv2.IMREAD_UNCHANGED)
                        if background is None:
                            print(f"Error loading background: {background_path}")
                            continue

                        data = im_1 - background
                        data = data * flatfield_shape
                        # Ajustar el tamaño de data si es necesario
                        if data.shape != biospace_data['data'][:, :, lambda_ind, scatter_ind, yaw_ind, roll_ind, 0].shape:
                            print(f"Shape mismatch: data shape {data.shape}, target shape {biospace_data['data'][:, :, lambda_ind, scatter_ind, yaw_ind, roll_ind, 0].shape}")
                            continue
                        biospace_data['data'][:, :, lambda_ind, scatter_ind, yaw_ind, roll_ind, 0] = data / (
                                biospace_data['exp_time'] * biospace_data['linear_gain'] * biospace_data['reference']
                        )

    biospace_data['x'] = np.arange(1, height + 1) * biospace_data['resolution']
    biospace_data['y'] = np.arange(1, width + 1) * biospace_data['resolution']


    return biospace_data


#-----------------------------------------------------------------------------------------------------
# Definimos variables necesarias para continuar la ejecución
lambda_LEDs = np.array([365, 405, 430, 490, 525, 630, 810, 940])  # Ejemplo de longitudes de onda
resolution = 1
# Importar datos desde las carpetas.
local_path = Path(r'/content/drive/MyDrive/HyperPi_measurements')

ref_folder_copol = local_path / '2023-12-06_1117_00_Copol_Teflon'
ref_folder_depol = local_path / '2023-12-06_1111_06_Depol_Teflon'
sample_folder_copol = local_path / 'Copol_Wings'
sample_folder_depol = local_path / 'Depol Wings'

reference, flatfield_shape = read_biospace_reference(ref_folder_copol, 0.7, 0)
biospace_data = read_biospace_data(sample_folder_copol, reference, flatfield_shape)
sample_depol = read_biospace_data(sample_folder_depol, reference, flatfield_shape)
biospace_data.data[..., 1] = sample_depol.data
biospace_data.polarization_angles = [0, 90]

# Reemplazar valores negativos por 0 y almacenar los datos.
biospace_data.data = np.maximum(biospace_data.data, 0)

#-----------------------------------------------------------------------------------------------------

# Imagen monocromática.
mono_image = plt.figure('Monochromatic Image')

# Seleccionar ángulos de la muestra.
scatter_angle_index = 1
yaw_angle_index = 1
roll_angle_index = 1
mono_wavelength = 8
print(f'Scatter angle: {biospace_data.scatter_angles[scatter_angle_index]}')
print(f'Yaw angle: {biospace_data.yaw_angles[yaw_angle_index]}')
print(f'Roll angle: {biospace_data.roll_angles[roll_angle_index]}')
print(f'Wavelength: {biospace_data.wavelengths[mono_wavelength]}')

# Generación de la imagen.
im_xy = biospace_data.data[..., mono_wavelength, scatter_angle_index, yaw_angle_index, roll_angle_index, 0]
im_xy = np.maximum(im_xy, 0)
im_for_visualization = np.sqrt(im_xy)
plt.imshow(im_for_visualization, cmap='gray', norm=Normalize(vmin=0, vmax=1))
plt.colorbar()
plt.xlabel('x (pixel)')
plt.ylabel('y (pixel)')
plt.show()


#-----------------------------------------------------------------------------------------------------

# Imagen en falso color.
false_color_image = plt.figure('False Color Image')

# Seleccionar ángulos de la muestra.
r_wavelength = 7
g_wavelength = 6
b_wavelength = 5
print(f'Scatter angle: {biospace_data.scatter_angles[scatter_angle_index]}')
print(f'Yaw angle: {biospace_data.yaw_angles[yaw_angle_index]}')
print(f'Roll angle: {biospace_data.roll_angles[roll_angle_index]}')
print(f'Wavelengths: R({biospace_data.wavelengths[r_wavelength]}) G({biospace_data.wavelengths[g_wavelength]}) B({biospace_data.wavelengths[b_wavelength]})')

# Generación de la imagen.
false_color_im = np.stack([
    biospace_data.data[..., r_wavelength, scatter_angle_index, yaw_angle_index, roll_angle_index, 0],
    biospace_data.data[..., g_wavelength, scatter_angle_index, yaw_angle_index, roll_angle_index, 0],
    biospace_data.data[..., b_wavelength, scatter_angle_index, yaw_angle_index, roll_angle_index, 0]
], axis=-1)
false_color_im = np.maximum(false_color_im, 0)
plt.imshow(np.sqrt(false_color_im))
plt.xlabel('x (mm)')
plt.ylabel('y (mm)')
plt.title(f'R: {biospace_data.wavelengths[r_wavelength]} nm, G: {biospace_data.wavelengths[g_wavelength]} nm, B: {biospace_data.wavelengths[b_wavelength]} nm')
plt.show()


#-----------------------------------------------------------------------------------------------------

# Imagen del grado de polarización lineal (DoLP).
dolp_image = plt.figure('Degree of Linear Polarization Image')

# Seleccionar ángulos de la muestra.
dolp_wavelength = 4
print(f'Scatter angle: {biospace_data.scatter_angles[scatter_angle_index]}')
print(f'Yaw angle: {biospace_data.yaw_angles[yaw_angle_index]}')
print(f'Roll angle: {biospace_data.roll_angles[roll_angle_index]}')
print(f'Wavelength: {biospace_data.wavelengths[dolp_wavelength]}')

# Generación de la imagen.
pol_falsecolor = np.stack([
    biospace_data.data[..., dolp_wavelength, scatter_angle_index, yaw_angle_index, roll_angle_index, 1],
    biospace_data.data[..., dolp_wavelength, scatter_angle_index, yaw_angle_index, roll_angle_index, 0] -
    biospace_data.data[..., dolp_wavelength, scatter_angle_index, yaw_angle_index, roll_angle_index, 1],
    np.zeros_like(biospace_data.data[..., dolp_wavelength, scatter_angle_index, yaw_angle_index, roll_angle_index, 1])
], axis=-1)
plt.imshow(pol_falsecolor)
plt.title('R = depol, G = copol-depol')
plt.show()

# Dibujar una Región de Interés (RoI).
plt.figure(false_color_image.number)
print('Image with Region of Interest (RoI)')

# Creación de la RoI.
mask_body = make_mask()

#-----------------------------------------------------------------------------------------------------

# Espectro de la RoI.
roi_spectrum = plt.figure('RoI Spectrum')

# Seleccionar ángulos de la muestra.
print(f'Scatter angle: {biospace_data.scatter_angles[scatter_angle_index]}')
print(f'Yaw angle: {biospace_data.yaw_angles[yaw_angle_index]}')
print(f'Roll angle: {biospace_data.roll_angles[roll_angle_index]}')

# Generación del espectro.
spectrum_matrix = biospace_data.data[..., scatter_angle_index, yaw_angle_index, roll_angle_index, 0]
spectrum_matrix *= mask_body
spectrum = np.sum(spectrum_matrix, axis=(0, 1)) / np.sum(mask_body)
spectrum *= 100
plt.plot(biospace_data.wavelengths, spectrum, 'k.-', markersize=12)
plt.xlabel('Wavelength [nm]')
plt.ylabel('Reflectance [%]')
plt.xlim(300, 1000)
plt.xticks(np.arange(300, 1100, 100))
plt.grid(False)
plt.show()

# Tabla de datos.
print(np.column_stack([biospace_data.wavelengths, spectrum]))

#-----------------------------------------------------------------------------------------------------

# Bucle sobre un ángulo para generar un gif.
loop_angle_gif = plt.figure('Loop gif')

select_angle = 2
print(f'Scatter angle: {biospace_data.scatter_angles[scatter_angle_index]}')
print(f'Yaw angle: {biospace_data.yaw_angles[yaw_angle_index]}')
print(f'Roll angle: {biospace_data.roll_angles[roll_angle_index]}')
print(f'Wavelengths: R({biospace_data.wavelengths[r_wavelength]}) G({biospace_data.wavelengths[g_wavelength]}) B({biospace_data.wavelengths[b_wavelength]})')

# Generación del gif.
rot_angle = None
if select_angle == 1:
    rot_angle = biospace_data.roll_angles
elif select_angle == 2:
    rot_angle = biospace_data.yaw_angles
elif select_angle == 3:
    rot_angle = biospace_data.scatter_angles
else:
    print('Error occurred')

frames = []
for angle in rot_angle:
    if select_angle == 1:
        false_color_im = np.stack([
            biospace_data.data[..., r_wavelength, scatter_angle_index, yaw_angle_index, angle, 0],
            biospace_data.data[..., g_wavelength, scatter_angle_index, yaw_angle_index, angle, 0],
            biospace_data.data[..., b_wavelength, scatter_angle_index, yaw_angle_index, angle, 0]
        ], axis=-1)
    elif select_angle == 2:
        false_color_im = np.stack([
            biospace_data.data[..., r_wavelength, scatter_angle_index, angle, roll_angle_index, 0],
            biospace_data.data[..., g_wavelength, scatter_angle_index, angle, roll_angle_index, 0],
            biospace_data.data[..., b_wavelength, scatter_angle_index, angle, roll_angle_index, 0]
        ], axis=-1)
    elif select_angle == 3:
        false_color_im = np.stack([
            biospace_data.data[..., r_wavelength, angle, yaw_angle_index, roll_angle_index, 0],
            biospace_data.data[..., g_wavelength, angle, yaw_angle_index, roll_angle_index, 0],
            biospace_data.data[..., b_wavelength, angle, yaw_angle_index, roll_angle_index, 0]
        ], axis=-1)
    plt.imshow(false_color_im)
    if select_angle == 1:
        plt.title(f'Roll angle: {angle}°')
    elif select_angle == 2:
        plt.title(f'Yaw angle: {angle}°')
    elif select_angle == 3:
        plt.title(f'Scatter angle: {angle}°')
    plt.xlabel('x (mm)')
    plt.ylabel('y (mm)')

    plt.draw()
    frame = np.frombuffer(plt.gcf().canvas.tostring_rgb(), dtype='uint8')
    frames.append(frame.reshape(plt.gcf().canvas.get_width_height()[::-1] + (3,)))

# Guardar gif.
gif(local_path / 'GIF_loop.gif', delay_time=1/15, loop_count=float('inf'), frame=frames)

print('GIF saved successfully!')


#-----------------------------------------------------------------------------------------------------

# Bucle sobre las longitudes de onda para generar un GIF.
loop_wave_gif = plt.figure('Loop Wavelength')

# Seleccionar ángulos de la muestra.
scatter_angle_index = 1
yaw_angle_index = 6
roll_angle_index = 1
print(f'Scatter angle: {biospace_data.scatter_angles[scatter_angle_index]}')
print(f'Yaw angle: {biospace_data.yaw_angles[yaw_angle_index]}')
print(f'Roll angle: {biospace_data.roll_angles[roll_angle_index]}')

# Generar el GIF.
frames = []
for wavelength_idx in range(len(biospace_data.wavelengths)):
    mono_im = biospace_data.data[..., wavelength_idx, scatter_angle_index, yaw_angle_index, roll_angle_index, 1]
    plt.imshow(np.sqrt(mono_im), cmap='jet', norm=Normalize(vmin=0, vmax=1))
    plt.colorbar()
    plt.title(f'Wavelength: {biospace_data.wavelengths[wavelength_idx]} nm')
    plt.xlabel('x (mm)')
    plt.ylabel('y (mm)')

    plt.draw()
    frame = np.frombuffer(plt.gcf().canvas.tostring_rgb(), dtype='uint8')
    frames.append(frame.reshape(plt.gcf().canvas.get_width_height()[::-1] + (3,)))

# Guardar GIF.
gif_path = local_path / 'wave_wing_blom_angle_25.gif'
imageio.mimsave(gif_path, frames, fps=1)  # Ajustar fps según sea necesario
print(f'GIF saved successfully at {gif_path}!')

#-----------------------------------------------------------------------------------------------------

# Gráfica polar
pol_plot = plt.figure('Polar plot')

# Seleccionar ángulos de la muestra.
scatter_angle_index = 1
yaw_angle_index = 1
roll_angle_index = 1
select_angle = 2
pol_wavelength = 3
print(f'Scatter angle: {biospace_data.scatter_angles[scatter_angle_index]}')
print(f'Yaw angle: {biospace_data.yaw_angles[yaw_angle_index]}')
print(f'Roll angle: {biospace_data.roll_angles[roll_angle_index]}')
print(f'Wavelength: {biospace_data.wavelengths[pol_wavelength]}')

# Generación de la gráfica polar.
ax = plt.subplot(projection='polar')

if select_angle == 1:
    data_copol = np.mean(biospace_data.data[..., pol_wavelength, scatter_angle_index, yaw_angle_index, :, 1], axis=(0, 1))
    data_depol = np.mean(biospace_data.data[..., pol_wavelength, scatter_angle_index, yaw_angle_index, :, 2], axis=(0, 1))
    plot_angles = np.radians(biospace_data.roll_angles)
elif select_angle == 2:
    data_copol = np.mean(biospace_data.data[..., pol_wavelength, scatter_angle_index, :, roll_angle_index, 1], axis=(0, 1))
    data_depol = np.mean(biospace_data.data[..., pol_wavelength, scatter_angle_index, :, roll_angle_index, 2], axis=(0, 1))
    plot_angles = np.radians(biospace_data.yaw_angles)
elif select_angle == 3:
    data_copol = np.mean(biospace_data.data[..., pol_wavelength, :, yaw_angle_index, roll_angle_index, 1], axis=(0, 1))
    data_depol = np.mean(biospace_data.data[..., pol_wavelength, :, yaw_angle_index, roll_angle_index, 2], axis=(0, 1))
    plot_angles = np.radians(biospace_data.scatter_angles)
else:
    raise ValueError('Error occurred')

ax.plot(plot_angles, data_copol, 'b.-', markersize=12, label='Copol')
ax.plot(plot_angles, data_depol, 'r.-', markersize=12, label='Depol')
ax.legend()
ax.set_rlabel_position(-22.5)  # Ajustar la posición del label radial si es necesario
ax.set_xlabel('Degrees (°)')
ax.set_ylabel('Intensity')

plt.show()
