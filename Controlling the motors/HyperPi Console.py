import RPi.GPIO as GPIO
import time
import tkinter as tk

try:
    GPIO.setmode(GPIO.BOARD)  # Use physical pin numbering

    #--------------------------------------------------
    #Initializing window

    window = tk.Tk()
    window.title("HyperPi Console")

    window.rowconfigure(0, minsize=800, weight=1)
    window.columnconfigure(1, minsize=800, weight=1)

    image = tk.Frame(window, relief = tk.SUNKEN) #define the right-side of the console, where image is shown
    frm_buttons = tk.Frame(window, relief = tk.RAISED, bd=2) #define the left-side of the console, where buttons are shown

    #end Initializing window
    #----------------------------------------------------
    #Entering custom pins layouts

    pins = {"Sampler" : 0,
            "Polarizer" : 0}

    def set_pins():
        try:
            pins["Sampler"] = int(sampler_pin.get())
            pins["Polarizer"] = int(polarizer_pin.get())
            print("\nPins are set to")
            
            for key, value in pins.items():
                print(key,value,sep = " pin : ")
                GPIO.setup(value, GPIO.OUT) #set out pins
        except:
            print("Please, enter integer values")

    sampler_label = tk.Label(frm_buttons, text = "Sampler pin :")
    sampler_label.grid(row = 0, column = 0, sticky ="ew", padx = 5, pady = 5)

    polarizer_label = tk.Label(frm_buttons, text = "Polarizer pin :")
    polarizer_label.grid(row = 1, column = 0, sticky = "ew", padx = 5)

    sampler_pin = tk.Entry(frm_buttons, bg = "white", fg = "black")
    sampler_pin.grid(row = 0, column = 1, sticky = "ew", padx = 5, pady = 5)

    polarizer_pin = tk.Entry(frm_buttons, bg = "white", fg = "black")
    polarizer_pin.grid(row = 1, column = 1, sticky = "ew", padx = 5)

    btn_set_pins = tk.Button(frm_buttons, text="Set Pins", command = set_pins)
    btn_set_pins.grid(row = 2, column = 0, sticky = "ew", padx = 5, pady = 5)

    #end entering custom pins layouts and functions
    #--------------------------------------------------
    #Moving the motors to custom angles

    def set_angle(angle, servo_pin):
        if 0 <= angle <= 180:
            try:
                servo = GPIO.PWM(servo_pin, 50)  
                servo.start(0) #start servo
                duty_cycle = 2 + (angle / 19)
                servo.ChangeDutyCycle(duty_cycle)
                time.sleep(0.5)
                servo.ChangeDutyCycle(0)
                servo.stop()
            except:
                print("An error ocurred at set_angle function")
        else:
            print("Only angles between 0 and 180 degrees are allowed")

    sampler_angle = tk.Entry(frm_buttons, bg = "white", fg = "black")
    sampler_angle.grid(row = 3, column = 1, sticky = "ew", padx = 5, pady = 5)

    btn_set_sampler_angle = tk.Button(frm_buttons, text = "Move Sampler",
                                      command = lambda: set_angle(float(sampler_angle.get()), pins["Sampler"]))
    btn_set_sampler_angle.grid(row = 3, column = 0, sticky = "ew", padx = 5, pady = 5)

    polarizer_angle = tk.Entry(frm_buttons, bg = "white", fg = "black")
    polarizer_angle.grid(row = 4, column = 1, sticky = "ew", padx = 5)

    btn_set_polarizer_angle = tk.Button(frm_buttons, text = "Move Polarizer",
                                        command = lambda: set_angle(float(polarizer_angle.get()), pins["Polarizer"]))
    btn_set_polarizer_angle.grid(row = 4, column = 0, sticky = "ew", padx = 5)

    #end moving the motors to custom angles
    #--------------------------------------------------
    frm_buttons.grid(row=0, column=0, sticky="ns")
    image.grid(row=0, column=1, sticky="nsew")

    window.mainloop()

finally:
    GPIO.cleanup()