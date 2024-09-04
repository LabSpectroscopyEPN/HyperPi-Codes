#Este codigo contiene funciones para controlar el apagado
#de los pines del arduino nano conectados al modulo de reles

import smbus
import time

# Dirección I2C del Arduino
ARDUINO_ADDRESS = 0x08
bus = smbus.SMBus(1)

# Función para apagar un pin
def control_pin(pin, state):
    try:
        bus.write_i2c_block_data(ARDUINO_ADDRESS, pin, [state])
        time.sleep(1)
    except Exception as e:
        print(f"Error: {e}")

# Apagar el pin especificado por el usuario
while True:
    try:
        num = int(input('Ingrese el pin que desea apagar: '))
        control_pin(num, 0)  # Apagar el pin
    except ValueError:
        print("Por favor, ingresa un número válido.")
