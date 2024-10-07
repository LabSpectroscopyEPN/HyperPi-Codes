import RPi.GPIO as GPIO
import time
import os
from datetime import datetime
import tkinter as tk
from tkinter import filedialog
from picamera2 import Picamera2,Preview
from libcamera import controls
import threading
import smbus


class CameraApp:
    def __init__(self, root):
        self.root = root
        GPIO.setmode(GPIO.BOARD)  # Use physical pin numbering
        self.bus = smbus.SMBus(1)
        self.pins = {"Sampler" : 0,
                     "Polarizer" : 0,
                     "LED Motor": 0} # initialize the pins dictionary
        self.width = 800
        self.height = 600
        self.camera_controls = {"AwbEnable": False,
                                "ColourGains": (1.0, 1.0),
                                "ExposureTime":100000,
                                "AnalogueGain":1.0,
                                "AfMode":0,
                                "AfTrigger":0,
                                "LensPosition":1.0,
                                "Brightness":0.0,
                                "Contrast":1.0,
                                "Saturation":1.0,
                                "Sharpness":1.0} # initialize the camera controls dictionary
        self.preview_thread = None # thread for start and stop preview
        self.stop_preview_event = threading.Event() # defining an event
        self.picam2 = Picamera2() # create a picamera2 object
        
        self.root.title("HyperPi Project")

        # window configuration
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight = 1, minsize = 350)
        self.root.columnconfigure(1, weight = 1, minsize = 400)
        self.root.columnconfigure(2, weight = 1, minsize = 350)
        
        # define the right-side of the console, where measure controls are shown
        self.right_side = tk.Frame(self.root, relief = tk.RAISED, bd=2)
        # define the mid-column part of the console, where the camera controls are shown
        self.mid_column = tk.Frame(self.root, relief = tk.RAISED, bd=2)
        # define the left-side of the console, where pins and other controlls are shown 
        self.left_side = tk.Frame(self.root, relief = tk.RAISED, bd=2)

        # adding the sides to the window
        self.left_side.grid(row=0, column=0, sticky="nsew")
        self.mid_column.grid(row=0, column=1, sticky="nsew")
        self.right_side.grid(row=0, column=2, sticky="nsew")

        #----------------------------------------------------
        # Entering custom pins layouts
        
        self.pin_layout_frame = tk.Frame(self.left_side, relief = tk.RAISED, bd = 2)
        self.pin_layout_frame.grid(row = 0, column = 0, sticky = "nsew")
        
        tk.Label(self.pin_layout_frame, text = "Sampler pin :").grid(row = 0, column = 0,
                                                                     sticky = "e", padx = 5, pady = 5)

        tk.Label(self.pin_layout_frame, text = "Polarizer pin :").grid(row = 1, column = 0,
                                                                       sticky = "e", padx = 5, pady = 5)
        
        tk.Label(self.pin_layout_frame, text = "Motor pin :").grid(row = 2, column = 0,
                                                                   sticky ="e", padx = 5, pady = 5)

        self.sampler_pin = tk.Entry(self.pin_layout_frame, bg = "white", fg = "black", width = 25)
        self.sampler_pin.grid(row = 0, column = 1, sticky = "ns", padx = 5, pady = 5)
        self.sampler_pin.insert(0,"40")

        self.polarizer_pin = tk.Entry(self.pin_layout_frame, bg = "white", fg = "black", width = 25)
        self.polarizer_pin.grid(row = 1, column = 1, sticky = "ns", padx = 5, pady = 5)
        self.polarizer_pin.insert(0,"38")
        
        self.motor_pin = tk.Entry(self.pin_layout_frame, bg = "white", fg = "black", width = 25)
        self.motor_pin.grid(row = 2, column = 1, sticky = "ns", padx = 5, pady = 5)
        self.motor_pin.insert(0,"36")
        
        self.set_pins()
        
        tk.Button(self.pin_layout_frame, text="Set Pins",
                  command = self.set_pins, width = 20).grid(row = 3, column = 0,
                                                            columnspan = 2, sticky = "ns", padx = 5, pady = 5)
        
        # end entering custom pins layouts
        #--------------------------------------------------
        # Moving the motors to custom angles
        
        self.servo_controls_layout = tk.Frame(self.left_side, relief = tk.RAISED, bd=2)
        self.servo_controls_layout.grid(row = 1, column = 0, sticky = "ew")
        
        self.sampler_angle = tk.Entry(self.servo_controls_layout, bg = "white", fg = "black")
        self.sampler_angle.grid(row = 0, column = 1, sticky = "ew", padx = 5, pady = 5)

        tk.Button(self.servo_controls_layout, text = "Move Sampler",
                  command = lambda: self.set_angle(float(self.sampler_angle.get()),self.pins["Sampler"])).grid(row = 0, column = 0,
                                                                                                               sticky = "ew", padx = 5, pady = 5)

        self.polarizer_angle = tk.Entry(self.servo_controls_layout, bg = "white", fg = "black")
        self.polarizer_angle.grid(row = 1, column = 1, sticky = "ew", padx = 5, pady = 5)

        tk.Button(self.servo_controls_layout, text = "Move Polarizer",
                  command = lambda: self.set_angle(float(self.polarizer_angle.get()), self.pins["Polarizer"])).grid(row = 1, column = 0,
                                                                                                                    sticky = "ew", padx = 5, pady = 5)

        self.motor_angle = tk.Entry(self.servo_controls_layout, bg = "white", fg = "black")
        self.motor_angle.grid(row = 2, column = 1, sticky = "ew", padx = 5, pady = 5)

        tk.Button(self.servo_controls_layout, text = "Move LEDs Motor",
                  command = lambda: self.set_angle(float(self.motor_angle.get()), self.pins["LED Motor"])).grid(row = 2, column = 0,
                                                                                                                sticky = "ew", padx = 5, pady = 5)

        # End moving the motors to custom angles
        #--------------------------------------------------
        # Adding a preview controls
        
        tk.Button(self.mid_column, text = "Select controls file :",
                  command = self.read_controls_file).grid(row = 0, column = 0,
                                                     sticky = "ew", padx = 5, pady = 5)
        
        self.control_file_entry = tk.Entry(self.mid_column, bg = "white", fg = "black")
        self.control_file_entry.grid(row = 0, column = 1, sticky = "ew", padx = 5, pady = 5)
        
        self.preview_layout = tk.Frame(self.mid_column, relief = tk.GROOVE, bd=2)
        self.preview_layout.grid(row = 1, column = 0, columnspan = 2, sticky = "ns")
        
        tk.Label(self.preview_layout, text = "Width :").grid(row = 0, column = 0,
                                                             sticky = "e", padx = 5, pady = 5)
        
        self.width_resolution = tk.Entry(self.preview_layout, bg = "white", fg = "black", width = 25)
        self.width_resolution.grid(row = 0, column = 1, sticky = "ns", padx = 5, pady = 5)
        
        tk.Label(self.preview_layout, text = "Height :").grid(row = 1, column = 0,
                                                              sticky = "e", padx = 5, pady = 5)
        
        self.height_resolution = tk.Entry(self.preview_layout, bg = "white", fg = "black", width = 25)
        self.height_resolution.grid(row = 1, column = 1, sticky = "ns", padx = 5, pady = 5)
        
        self.btn_start_preview = tk.Button(self.preview_layout, text="Start Preview",
                                           command=self.start_preview,
                                           width = 15)
        self.btn_start_preview.grid(row=3, column=0, padx=5, pady=5)

        self.btn_stop_preview = tk.Button(self.preview_layout, text="Stop Preview",
                                          command=self.stop_preview_loop,
                                          state="disabled",
                                          width = 15)
        self.btn_stop_preview.grid(row=3, column=1, padx=5, pady=5)
        
        tk.Label(self.preview_layout, text = "Exposure time:").grid(row = 4, column = 0,
                                                                     sticky = "e", padx = 5, pady = 5)
        
        self.exposure_time = tk.Entry(self.preview_layout, bg = "white", fg = "black", width = 25)
        self.exposure_time.grid(row = 4, column = 1, sticky = "ns", padx = 5, pady = 5)
        
        
        tk.Label(self.preview_layout, text = "Analogue gain :").grid(row = 5, column = 0,
                                                                     sticky = "e", padx = 5, pady = 5)
        
        self.analogue_gain = tk.Entry(self.preview_layout, bg = "white", fg = "black", width = 25)
        self.analogue_gain.grid(row = 5, column = 1, sticky = "ns", padx = 5, pady = 5)
        
        
        tk.Label(self.preview_layout, text = "Lens Position :").grid(row = 6, column = 0,
                                                                     sticky = "e", padx = 5, pady = 5)
        
        self.lens_position = tk.Entry(self.preview_layout, bg = "white", fg = "black", width = 25)
        self.lens_position.grid(row = 6, column = 1, sticky = "ns", padx = 5, pady = 5)        
        
        self.btn_set_controls = tk.Button(self.preview_layout, text="Set Camera Controls", command = self.set_camera_controls, width = 20)
        self.btn_set_controls.grid(row = 7, column = 0, columnspan = 2, sticky = "ns", padx = 5, pady = 5)

        # End preview controls
        #--------------------------------------------------
        # Adding measurement controls
        
        tk.Button(self.right_side, text = "Select folder :",
                  command = self.select_folder).grid(row = 0, column = 0,
                                                     sticky = "ew", padx = 5, pady = 5)
        
        self.parent_folder_entry = tk.Entry(self.right_side, bg = "white", fg = "black")
        self.parent_folder_entry.grid(row = 0, column = 1, sticky = "ew", padx = 5, pady = 5)
        
        self.measurement_controls_layout = tk.Frame(self.right_side, relief = tk.GROOVE, bd=2)
        self.measurement_controls_layout.grid(row = 1, column = 0, columnspan = 2, sticky = "ns")
        
        tk.Label(self.measurement_controls_layout,
                 text = "Insert sampler angle protocol as begin-end-step,\n or angle1, angle2, angle3,...").grid(row = 0, column = 0,
                                                                                 sticky = "ns", padx = 5, pady = 5)
        self.sampler_protocol = tk.Entry(self.measurement_controls_layout, bg = "white", fg = "black", width = 25)
        self.sampler_protocol.grid(row = 1, column = 0, sticky = "ns", padx = 5, pady = 5)
        self.sampler_protocol.insert(0, "0")
        
        tk.Label(self.measurement_controls_layout,
                 text = "Insert polarizer angle protocol as begin-end-step,\n or angle1, angle2, angle3,...").grid(row = 2, column = 0,
                                                                                 sticky = "ns", padx = 5, pady = 5)
        self.polarizer_protocol = tk.Entry(self.measurement_controls_layout, bg = "white", fg = "black", width = 25)
        self.polarizer_protocol.grid(row = 3, column = 0, sticky = "ns", padx = 5, pady = 5)
        self.polarizer_protocol.insert(0, "0,90")
        
        tk.Button(self.measurement_controls_layout, text = "Start Measurement",
                  command = self.measure, width = 30).grid(row = 4, column = 0, sticky = "ns", padx = 5, pady = 5)
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
                duty_cycle = 2 + (angle / 18)
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
        print("\nPreview has ended")

    def preview_loop(self):
        self.picam2.start_preview(Preview.QTGL)
        self.set_camera_configuration()
        self.set_camera_controls()
        self.picam2.start()
        while not self.stop_preview_event.is_set():
            print("Preview displayed")
            time.sleep(10)
            continue
        self.picam2.stop_preview()
        self.picam2.stop()
    
    def set_camera_configuration(self):
        width = self.width_resolution.get()
        height = self.height_resolution.get()
        
        if (width == '') or (height == ''):
            self.width = 800
            self.width_resolution.delete(0,tk.END)
            self.width_resolution.insert(0,self.width)
            self.height = 600
            self.height_resolution.delete(0,tk.END)
            self.height_resolution.insert(0,self.height)
        else:
            self.width = int(width)
            self.height = int(height)
            
        print(f"Current resolution is : {width}x{height}")
        self.picam2.configure(self.picam2.create_preview_configuration({"size":(self.width,self.height)}))

    def set_camera_controls(self):
        exposure_time = self.exposure_time.get()
        analogue_gain = self.analogue_gain.get()
        lens_position = self.lens_position.get()
        
        if exposure_time == '':
            self.exposure_time.delete(0,tk.END)
            self.exposure_time.insert(0,self.camera_controls["ExposureTime"])
        else:
            self.camera_controls["ExposureTime"] = int(exposure_time)
        if analogue_gain == '':
            self.analogue_gain.delete(0,tk.END)
            self.analogue_gain.insert(0,self.camera_controls["AnalogueGain"])
        else:
            self.camera_controls["AnalogueGain"] = float(analogue_gain)    
        if lens_position == '':
            self.lens_position.delete(0,tk.END)
            self.lens_position.insert(0,self.camera_controls["LensPosition"])
        else:
            self.camera_controls["LensPosition"] = float(lens_position)

        self.picam2.set_controls(self.camera_controls)
        for key, value in self.camera_controls.items():
            print(key,value,sep=" : ")
            
    def read_controls_file(self):
        file_path = filedialog.askopenfilename(title="Select you control file as .txt",
                                               filetypes=[("Text files","*.txt")])
        if file_path:
            self.control_file_entry.delete(0, tk.END)
            self.control_file_entry.insert(0, file_path)
            
            with open(file_path, 'r') as file:
                # Read the content of the file
                content = [line.strip().split() for line in file.readlines()]
            # Create a dictionary to store the camera controls
            camera_controls = {}
            for line in content:
                control_name = line[0]
                control_value = int(line[1]) if line[2]=="Int" else (float(line[1]) if line[2]=="Float" else "NonValid")
                camera_controls[control_name] = control_value
            
            try:
                self.width = camera_controls["Width"]
                self.height = camera_controls["Height"]
                self.width_resolution.delete(0,tk.END)
                self.width_resolution.insert(0,self.width)
                self.height_resolution.delete(0,tk.END)
                self.height_resolution.insert(0,self.height)
                del camera_controls["Width"]
                del camera_controls["Height"]
            except:
                print("Non wide nor height available, please check code")
                
            self.camera_controls = camera_controls
            self.exposure_time.delete(0,tk.END)
            self.exposure_time.insert(0,self.camera_controls["ExposureTime"])
            self.analogue_gain.delete(0,tk.END)
            self.analogue_gain.insert(0,self.camera_controls["AnalogueGain"])
            self.lens_position.delete(0,tk.END)
            self.lens_position.insert(0,self.camera_controls["LensPosition"])
            self.set_camera_controls()
            
    def select_folder(self):
        folder_path = filedialog.askdirectory()
        if folder_path:
            self.parent_folder_entry.delete(0, tk.END)
            self.parent_folder_entry.insert(0, folder_path)
            self.parent_folder = self.parent_folder_entry.get()
            print("Current saving path: ", self.parent_folder)
            
    def measure(self):
        if self.stop_preview_event.is_set():
            self.stop_preview_loop()
        
        pin_list = [2,3,4,5,6,7,8,9,10,11,12,14,15,16,17]
        #wavelength_list = [445, 490, 520, 560, 580, 600, 620, 660, 680, 730, 760, 800, 850, 880, 940, 980]
        wavelength_list = [445, 490, 520, 560, 580, 600, 620, 660, 680, 730, 800, 850, 880, 940, 980]
        
        sampler_angles = self.sampler_protocol.get()
        polarizer_angles = self.polarizer_protocol.get()
        
        if "-" in sampler_angles:
            sampler_angles = list(map(float,sampler_angles.strip().split("-")))
            sampler_angles = [sampler_angles[0] + sampler_angles[2]*i for i in range(1 + int((sampler_angles[1] - sampler_angles[0])/sampler_angles[2]))]
        elif "," in sampler_angles:
            sampler_angles = list(map(float,sampler_angles.strip().split(",")))
        else:
            sampler_angles = list(map(float,sampler_angles.strip().split()))
            
        if "-" in polarizer_angles:
            polarizer_angles = list(map(float,polarizer_angles.strip().split("-")))
            polarizer_angles = [polarizer_angles[0] + polarizer_angles[2]*i for i in range(1 + int((polarizer_angles[1] - polarizer_angles[0])/polarizer_angles[2]))]
        elif "," in polarizer_angles:
            polarizer_angles = list(map(float,polarizer_angles.strip().split(",")))
        else:
            polarizer_angles = list(map(float,polarizer_angles.strip().split()))
            
        for i,j in zip(sampler_angles,polarizer_angles):
            assert type(i) == float
            assert type(j) == float

        self.set_camera_configuration()
        preview_config = self.picam2.create_preview_configuration({"size":(self.width,self.height)})
        still_config = self.picam2.create_still_configuration({"size":(self.width,self.height)})
        
        self.picam2.configure(preview_config)
        self.picam2.start_preview(Preview.QTGL)
        self.set_camera_controls()
        self.picam2.start()
        time.sleep(7)
        
        print("Camera initialized")
        
        if polarizer_angles == [0.0,90.0]:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            new_folder = os.path.join(self.parent_folder, f"Measurement_{timestamp}")
            os.makedirs(new_folder, exist_ok=True)

            #save camera controls
            controls_file_path = os.path.join(new_folder, "Controls Setting.txt")
            
            # Rewrite the content of the file
            with open(controls_file_path, 'w') as file:
                for i,j in zip(["Width","Height"],[self.width,self.height]):
                    file.write(f"{i}\t{j}\t{'Int'} \n")
                # Write the content to the file
                for control, value in self.camera_controls.items():
                    line = f"{control}\t{value}\t{'Int' if type(value)==int else ('Float' if type(value)==float else 'NonValid')} \n"
                    file.write(line)
            
            for sampler in sampler_angles:
                #move sampler
                self.set_angle(sampler,self.pins["Sampler"])
                
                #wait
                time.sleep(1)
                
                #create copol and depol folders for this sampler angle
                copol_folder = os.path.join(new_folder, f"Copol_Sampler_{sampler}")
                os.makedirs(copol_folder, exist_ok=True)
                depol_folder = os.path.join(new_folder, f"Depol_Sampler_{sampler}")
                os.makedirs(depol_folder, exist_ok=True)
                
                #capture background picture
                #move leds motor
                self.set_angle(0, self.pins["LED Motor"])
                #move polarizer
                self.set_angle(0,self.pins["Polarizer"])
                time.sleep(1)
                #capture copol
                image_path = os.path.join(copol_folder, "background.jpg")
                self.picam2.switch_mode_and_capture_file(still_config, image_path)
                time.sleep(0.5)
                print("Copol taken")
                #move polarizer motor
                self.set_angle(90,self.pins["Polarizer"])
                time.sleep(1)
                image_path = os.path.join(depol_folder, "background.jpg")
                self.picam2.switch_mode_and_capture_file(still_config, image_path)
                time.sleep(0.5)
                print("Depol taken")
                    
                
                for led in range(15):
                    #move leds motor
                    self.set_angle(12*led, self.pins["LED Motor"])
                    
                    #turn on led
                    self.bus.write_i2c_block_data(0x08, pin_list[led], [0])
                    print("Led encendido")
                    
                    #move polarizer motor
                    self.set_angle(0,self.pins["Polarizer"])
                    
                    time.sleep(1)
                    
                    #capture copol
                    image_path = os.path.join(copol_folder, f"{wavelength_list[led]}.jpg")
                    self.picam2.switch_mode_and_capture_file(still_config, image_path)
                    time.sleep(0.5)
                    print("Copol taken")
                    
                    #move polarizer motor
                    self.set_angle(90,self.pins["Polarizer"])
                    
                    time.sleep(1)
                    
                    image_path = os.path.join(depol_folder, f"{wavelength_list[led]}.jpg")
                    self.picam2.switch_mode_and_capture_file(still_config, image_path)
                    time.sleep(0.5)
                    print("Depol taken")
                    
                    #turn of led
                    self.bus.write_i2c_block_data(0x08, pin_list[led], [1])                   
                    print("Led apagado")
                    time.sleep(1)
        
        self.picam2.stop_preview()
        self.picam2.stop()
        
        print("\nMeasurement concluded")
        
        
# end CameraApp class
try:
    window = tk.Tk()

    app = CameraApp(window)
    window.mainloop()
    
finally:
    print("\n","Bye","\n",sep=10*"-")
    GPIO.cleanup()

