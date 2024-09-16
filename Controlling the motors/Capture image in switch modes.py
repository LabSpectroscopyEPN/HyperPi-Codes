import os
from datetime import datetime
from picamera2 import Picamera2,Preview
import time

def capture_image_in_subfolder(parent_folder):
    if not os.path.exists(parent_folder):
        print(f"The folder '{parent_folder}' does not exist.")
        return

    # Create a new folder inside the provided path
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    new_folder = os.path.join(parent_folder, f"Angles_1_2_3_{timestamp}")
    os.makedirs(new_folder, exist_ok=True)
    print(f"New folder created: {new_folder}")

    # Initialize the camera
    picam2 = Picamera2()
    preview_config = picam2.create_preview_configuration()
    still_config = picam2.create_still_configuration()
    picam2.configure(preview_config)
    picam2.start_preview(Preview.QTGL)
    picam2.start()
    
    time.sleep(5)

    # Capture the image and save in the new folder
    image_filename = f"image_300_nm.jpg"
    image_path = os.path.join(new_folder, image_filename)
    picam2.switch_mode_and_capture_file(still_config, image_path)
    
    print(f"Image saved as {image_path}")
    time.sleep(5)
    
    picam2.stop()


parent_folder = "/home/hyperpi/Desktop/HyperPi/Results"
    
#probando
capture_image_in_subfolder(parent_folder)
