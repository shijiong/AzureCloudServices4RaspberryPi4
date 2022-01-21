import cv2
import numpy as np
import matplotlib.pylab as plt
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes
from azure.cognitiveservices.vision.computervision.models import VisualFeatureTypes
from msrest.authentication import CognitiveServicesCredentials
from azure.storage.blob import ContentSettings, BlobClient
from azure.iot.device import Message
from azure.iot.device.aio import IoTHubDeviceClient

import RPi.GPIO as GPIO
import asyncio

#Computer Vision
subscription_key = "Your Key"
endpoint = "https://***.cognitiveservices.azure.com/"
computervision_client = ComputerVisionClient(endpoint, CognitiveServicesCredentials(subscription_key))

# Set the size of the image (in pixels)
img_width = 1280
img_height = 720

camera = cv2.VideoCapture(0)
camera.set(cv2.CAP_PROP_FRAME_WIDTH, img_width)
camera.set(cv2.CAP_PROP_FRAME_HEIGHT, img_height)

# Select color for the bounding box
color = (0,255,0)
# Delay 5 second
DELAY = 5

async def main():
    # Initialize GPIO
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    GPIO.cleanup()
    GPIO.setup(4, GPIO.IN) #PIR
    print("Detection started. Press Ctrl-C to exit")
    while True:
        if GPIO.input(4): #motion detected
            try:                              
                ret, image = camera.read()
                cv2.imwrite('capture.jpg', image)
                # Open local image file
                read_image = open("capture.jpg", "rb")
                print("===== OCR Demo - camera =====")
                # Call API with image and raw response (allows you to get the operation location)
                read_response = computervision_client.read_in_stream(read_image, raw=True)
                # Get the operation location (URL with ID as last appendage)
                read_operation_location = read_response.headers["Operation-Location"]
                # Take the ID off and use to get results
                operation_id = read_operation_location.split("/")[-1]

                # Call the "GET" API and wait for the retrieval of the results
                while True:
                    read_result = computervision_client.get_read_result(operation_id)
                    if read_result.status.lower () not in ['notstarted', 'running']:
                        break
                    print ('Waiting for result...')
                    await asyncio.sleep(1)

                # Print results, line by line
                if read_result.status == OperationStatusCodes.succeeded:
                    for text_result in read_result.analyze_result.read_results:
                        for line in text_result.lines:
                            print(line.text)
                            print(line.bounding_box)
                            pts = np.array(line.bounding_box, np.int32).reshape((-1,1,2))
                            image = cv2.polylines(image, [pts], True, (0, 255, 0), 2)
                            cv2.imwrite('result.jpg', image)
                # show local image file
                img = cv2.imread('result.jpg') 
                cv2.imshow('result',img)
                if cv2.waitKey(1000) & 0xFF == ord('q'):
                    cv2.destroyAllWindows()
                    break                       
            except KeyboardInterrupt:
                print("Detection stopped")
                GPIO.cleanup()
                camera.release()
                break
if __name__ == '__main__':
    asyncio.run(main())