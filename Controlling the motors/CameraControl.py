import time

from picamera2 import Picamera2, Preview

picam2 = Picamera2()

preview_config = picam2.create_preview_configuration(main={"size":(1600,1200)})
picam2.configure(preview_config)

picam2.start_preview(Preview.QTGL)

picam2.start()

time.sleep(1)

# continuous focus, 1 for single "capture" and focus
picam2.set_controls({"AfMode": 2, "AfTrigger": 0, "LensPosition": 425})

time.sleep(20)

metadata = picam2.capture_file("test.jpg")
print(metadata)

picam2.close()
