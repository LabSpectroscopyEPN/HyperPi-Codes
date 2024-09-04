// Codigo para subir a Arduino Nano en comunicacion I2C con RaspberryPi

#include <Wire.h>

int digitalPins[] = {2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12};
int analogPins[] = {A0, A1, A2, A3, A6}; // A4 removido, A6 agregado

void setup() {
  Wire.begin(8); // Iniciar Arduino como esclavo I2C con dirección 8
  Wire.onReceive(receiveData); // Llamar a la función receiveData cuando se recibe un dato
  
  // Configurar todos los pines como salidas y encenderlos (HIGH)
  for (int i = 0; i < 11; i++) {
    pinMode(digitalPins[i], OUTPUT);
    digitalWrite(digitalPins[i], HIGH); // Encender todos los pines digitales
  }
  
  for (int i = 0; i < 5; i++) {
    pinMode(analogPins[i], OUTPUT);
    digitalWrite(analogPins[i], HIGH); // Encender todos los pines analógicos
  }
}

void loop() {
  // No hay nada que hacer en el loop
}

void receiveData(int byteCount) {
  while (Wire.available()) {
    int pin = Wire.read(); // Leer el pin
    int state = Wire.read(); // Leer el estado (HIGH o LOW)

    if (pin >= 2 && pin <= 12) {
      digitalWrite(pin, state); // Controlar pines digitales
    } else if (pin == 14 || pin == 15 || pin == 16 || pin == 17 || pin == 20) { // A0 - A3 corresponden a 14 - 17, A6 es 20
      digitalWrite(pin, state); // Controlar pines analógicos
    }
  }
}
