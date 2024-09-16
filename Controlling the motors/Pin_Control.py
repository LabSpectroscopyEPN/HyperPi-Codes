#Este codigo contiene funciones para controlar el apagado
#de los pines del arduino nano conectados al modulo de reles

import smbus
import time

# Dirección I2C del Arduino
ARDUINO_ADDRESS = 0x08
bus = smbus.SMBus(1)

# Pines usados
pinlist = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 14, 15, 16, 17]

# LEDs wavelenghts

# 445, 490, 520, 560, 580, 600, 620, 660, 680, 730, 760, 800, 850, 880, 940, 980

# Función para apagar un pin
def control_pin(pin, state):
    try:
        bus.write_i2c_block_data(ARDUINO_ADDRESS, pin, [state])
    except Exception as e:
        print(f"Error: {e}")

# Apagar el pin especificado por el usuario
# El modulo de reles tiene logica invertida
def pin_h_l(delay):
    while True:
        try:
            num = int(input('Ingrese el LED que desea encender: '))
            control_pin(pinlist[num], 0)  # Apagar el pin
            time.sleep(delay)
            control_pin(pinlist[num], 1)  # Encender el pin
        except ValueError:
            print("Por favor, ingresa un número válido.")

pin_h_l(0.5)
