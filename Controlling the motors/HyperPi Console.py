import RPi.GPIO as GPIO
import time
import tkinter as tk
from picamera2 import Picamera2,Preview
import threading


class CameraApp:
    def __init__(self, root):
        self.root = root
        GPIO.setmode(GPIO.BOARD)  # Use physical pin numbering
        self.pins = {"Sampler" : 0, "Polarizer" : 0, "LED Motor": 0} # initialize the pins dictionary
        self.preview_thread = None # thread for start and stop preview
        self.stop_preview_event = threading.Event() # defining an event
        self.picam2 = Picamera2() # create a picamera2 object
        
        self.root.title("HyperPi Project")

        # window configuration
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight = 1, minsize = 350)
        self.root.columnconfigure(1, weight = 1, minsize = 350)
        
        # define the right-side of the console, where camera controls are shown
        self.right_side = tk.Frame(self.root, relief = tk.RAISED, bd=2)
        #define the left-side of the console, where pins and other controlls are shown 
        self.left_side = tk.Frame(self.root, relief = tk.RAISED, bd=2)

        # adding both sides to the window
        self.left_side.grid(row=0, column=0, sticky="nsew")
        self.right_side.grid(row=0, column=1, sticky="nsew")

        #----------------------------------------------------
        # Entering custom pins layouts
        
        self.pin_layout_frame = tk.Frame(self.left_side, relief = tk.RAISED, bd = 2)
        self.pin_layout_frame.grid(row = 0, column = 0, sticky = "nsew")
        
        self.sampler_label = tk.Label(self.pin_layout_frame, text = "Sampler pin :")
        self.sampler_label.grid(row = 0, column = 0, sticky = "e", padx = 5, pady = 5)

        self.polarizer_label = tk.Label(self.pin_layout_frame, text = "Polarizer pin :")
        self.polarizer_label.grid(row = 1, column = 0, sticky = "e", padx = 5, pady = 5)
        
        self.motor_label = tk.Label(self.pin_layout_frame, text = "Motor pin :")
        self.motor_label.grid(row = 2, column = 0, sticky ="e", padx = 5, pady = 5)

        self.sampler_pin = tk.Entry(self.pin_layout_frame, bg = "white", fg = "black", width = 25)
        self.sampler_pin.grid(row = 0, column = 1, sticky = "ns", padx = 5, pady = 5)

        self.polarizer_pin = tk.Entry(self.pin_layout_frame, bg = "white", fg = "black", width = 25)
        self.polarizer_pin.grid(row = 1, column = 1, sticky = "ns", padx = 5, pady = 5)
        
        self.motor_pin = tk.Entry(self.pin_layout_frame, bg = "white", fg = "black", width = 25)
        self.motor_pin.grid(row = 2, column = 1, sticky = "ns", padx = 5, pady = 5)

        self.btn_set_pins = tk.Button(self.pin_layout_frame, text="Set Pins", command = self.set_pins, width = 20)
        self.btn_set_pins.grid(row = 3, column = 0, columnspan = 2, sticky = "ns", padx = 5, pady = 5)
        
        # end entering custom pins layouts
        #--------------------------------------------------
        # Moving the motors to custom angles
        
        self.servo_controls_layout = tk.Frame(self.left_side, relief = tk.RAISED, bd=2)
        self.servo_controls_layout.grid(row = 1, column = 0, sticky = "ew")
        
        self.sampler_angle = tk.Entry(self.servo_controls_layout, bg = "white", fg = "black")
        self.sampler_angle.grid(row = 0, column = 1, sticky = "ew", padx = 5, pady = 5)

        self.btn_set_sampler_angle = tk.Button(self.servo_controls_layout,
                                               text = "Move Sampler",
                                               command = lambda: self.set_angle(float(self.sampler_angle.get()), self.pins["Sampler"]))
        self.btn_set_sampler_angle.grid(row = 0, column = 0, sticky = "ew", padx = 5, pady = 5)

        self.polarizer_angle = tk.Entry(self.servo_controls_layout, bg = "white", fg = "black")
        self.polarizer_angle.grid(row = 1, column = 1, sticky = "ew", padx = 5)

        self.btn_set_polarizer_angle = tk.Button(self.servo_controls_layout,
                                                 text = "Move Polarizer",
                                                 command = lambda: self.set_angle(float(self.polarizer_angle.get()), self.pins["Polarizer"]))
        self.btn_set_polarizer_angle.grid(row = 1, column = 0, sticky = "ew", padx = 5)

        self.motor_angle = tk.Entry(self.servo_controls_layout, bg = "white", fg = "black")
        self.motor_angle.grid(row = 2, column = 1, sticky = "ew", padx = 5)

        self.btn_set_motor_angle = tk.Button(self.servo_controls_layout,
                                                 text = "Move LEDs Motor",
                                                 command = lambda: self.set_angle(float(self.motor_angle.get()), self.pins["LED Motor"]))
        self.btn_set_motor_angle.grid(row = 2, column = 0, sticky = "ew", padx = 5)

        # End moving the motors to custom angles
        #--------------------------------------------------
        # Adding a preview controls
        
        self.preview_layout = tk.Frame(self.right_side, relief = tk.RAISED, bd=2)
        self.preview_layout.grid(row = 0, column = 0, sticky = "ns")
        
        self.btn_start_preview = tk.Button(self.preview_layout, text="Start Preview",
                                           command=self.start_preview,
                                           width = 15)
        self.btn_start_preview.grid(row=0, column=0, padx=5, pady=5)

        self.btn_stop_preview = tk.Button(self.preview_layout, text="Stop Preview",
                                          command=self.stop_preview_loop,
                                          state="disabled",
                                          width = 15)
        self.btn_stop_preview.grid(row=0, column=1, padx=5, pady=5)

        # End preview controls
        #--------------------------------------------------
        
    #------------------------------------------------------
    #functions
        
    def set_pins(self):
        try:
            self.pins["Sampler"] = int(self.sampler_pin.get())
            self.pins["Polarizer"] = int(self.polarizer_pin.get())
            self.pins["LED Motor"] = int(self.motor_pin.get())
            print("\nPins are set to")
            
            for key, value in self.pins.items():
                print(key,value,sep = " pin : ")
                GPIO.setup(value, GPIO.OUT) #set out pins
        except:
            print("Please, enter integer values")
            
    def set_angle(self, angle, servo_pin):
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
        
    def start_preview(self):
        self.stop_preview_event.clear()
        self.preview_thread = threading.Thread(target=self.preview_loop)
        self.preview_thread.start()
        self.btn_start_preview.config(state="disabled")
        self.btn_stop_preview.config(state="normal")
        print("\nPreview is started")

    def stop_preview_loop(self):
        self.stop_preview_event.set()
        self.btn_start_preview.config(state="normal")
        self.btn_stop_preview.config(state="disabled")
        print("\nCapture loop has ended")

    def preview_loop(self):
        self.picam2.start_preview(Preview.QTGL)
        self.picam2.configure(self.picam2.create_preview_configuration(main={"size":(800,600)}))
        self.picam2.start()
        self.set_camera_configuration()
        while not self.stop_preview_event.is_set():
            print("Preview displayed")
            time.sleep(5)
            continue
        self.picam2.stop_preview()
        self.picam2.stop()
    
    def set_camera_configuration(self):
        self.picam2.set_controls({"AfMode": 2, "AfTrigger": 0, "LensPosition": 425})


# end CameraApp class
try:
    window = tk.Tk()

    app = CameraApp(window)
    window.mainloop()
    
finally:
    print("\n","Bye","\n",sep=10*"-")
    GPIO.cleanup()

