import RPi.GPIO as GPIO
import time

# Set up the GPIO
GPIO.setmode(GPIO.BOARD)  # Use physical pin numbering
servo_pin =  # Connect your servo data pin to GPIO 11 (Pin 11)

# Set up the servo pin
GPIO.setup(servo_pin, GPIO.OUT)
servo = GPIO.PWM(servo_pin, 50)  # 50Hz frequency for the servo

# Start PWM with the initial position at 0 degrees
servo.start(0)

def set_angle(angle):
    # The duty cycle is based on the angle; typically,
    #0 degrees = 2% duty cycle, and 180 degrees = 12% duty cycle
    duty_cycle = 2 + (angle / 18)
    GPIO.output(servo_pin, True) # don't really needed
    servo.ChangeDutyCycle(duty_cycle)
    time.sleep(0.5)
    GPIO.output(servo_pin, False) # don't really needed
    servo.ChangeDutyCycle(0)

try:
    while True:
        angle = float(input("Enter the angle (0-180): "))
        if 0 <= angle <= 180:
            set_angle(angle)
        else:
            print("Please enter a valid angle between 0 and 180.")

except KeyboardInterrupt:
    print("Program stopped by user.")

finally:
    servo.stop()
    GPIO.cleanup()
