import cv2
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
#Bolb Storage
conn_str="DefaultEndpointsProtocol=https;AccountName=***;AccountKey=***;BlobEndpoint=https://***.blob.core.windows.net/;QueueEndpoint=https://***.queue.core.windows.net/;TableEndpoint=https://***.table.core.windows.net/;FileEndpoint=https://myiotservicestorage.file.core.windows.net/;"
container_name="raspberrypic"
blob_name="face_detect"
blob_client = BlobClient.from_connection_string(conn_str, container_name, blob_name)

# Azure IotHub
CONNECTION_STRING = "HostName=***.azure-devices.net;DeviceId=***;SharedAccessKey=***"
# Create instance of the device client
iothub_client = IoTHubDeviceClient.create_from_connection_string(CONNECTION_STRING)
PAYLOAD = '{{"No. of faces": {face_num}}}'

# Set the size of the image (in pixels)
img_width = 1280
img_height = 720

camera = cv2.VideoCapture(1)
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
                local_image = open("capture.jpg", "rb")
                print("===== Detect Faces - camera =====")
                # Select visual features(s) you want
                local_image_features = ["faces"]
                # Call API with local image and features
                detect_faces_results_local = computervision_client.analyze_image_in_stream(local_image, local_image_features)
                
                #data formating
                data = PAYLOAD.format(face_num=len(detect_faces_results_local.faces))
                message = Message(data)
                # Send a message to the IoT hub
                print(f"Sending message to Azure IoTHub: {message}")
                await iothub_client.send_message(message)
                print("Message successfully sent")
                
                # Print results with confidence score
                print("Faces in the local image: ")
                if (len(detect_faces_results_local.faces) == 0):
                    print("No faces detected.")
                else:
                    for face in detect_faces_results_local.faces:
                        left = face.face_rectangle.left
                        top = face.face_rectangle.top
                        right = face.face_rectangle.left + face.face_rectangle.width
                        bottom = face.face_rectangle.top + face.face_rectangle.height         
                        print("'{}' of age {} at location {}, {}, {}, {}".format(face.gender, face.age, \
                        face.face_rectangle.left, face.face_rectangle.top, \
                        face.face_rectangle.left + face.face_rectangle.width, \
                        face.face_rectangle.top + face.face_rectangle.height))
                        result_image = cv2.rectangle(image,(left,top),(right,bottom),color,3)
                        cv2.putText(result_image, f"{face.gender},{face.age}", (int(left), int(top)-10), fontFace = cv2.FONT_HERSHEY_SIMPLEX, fontScale = 0.7, color = color, thickness = 2)
                        cv2.imwrite('result.jpg', result_image)
                    # show local image file
                    img = cv2.imread('result.jpg') 
                    cv2.imshow('result',img)
                    if cv2.waitKey(1000) & 0xFF == ord('q'):
                        cv2.destroyAllWindows()
                        break
                    # upload the image to Azure Blob Storage, Overwrite if it already exists!
                    image_content_setting = ContentSettings(content_type='image/jpeg')
                    with open("result.jpg", "rb") as data:
                        blob_client.upload_blob(data,overwrite=True,content_settings=image_content_setting)
                        print("Upload completed")                                                     
                    await asyncio.sleep(DELAY)
            except KeyboardInterrupt:
                print("Detection stopped")
                GPIO.cleanup()
                camera.release()
                break
if __name__ == '__main__':
    asyncio.run(main())