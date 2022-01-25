from azure.storage.blob import ContentSettings, BlobClient
from azure.iot.device import IoTHubDeviceClient, Message, MethodResponse
import os
from PIL import Image
import matplotlib.pyplot as plt
import time
import cv2
import board
import RPi.GPIO as GPIO
import dht11
import asyncio

# Azure IoThub
IoTHub_CONNECTION_STRING = "HostName=***.azure-devices.net;DeviceId=***;SharedAccessKey=***"
TEMPERATURE = 20.0
HUMIDITY = 60
PAYLOAD = '{{"temperature": {temperature}, "humidity": {humidity}, "PIR": {pir}}}'

#Azure Blob Storage
storage_conn_str="DefaultEndpointsProtocol=https;AccountName=***;AccountKey=***;BlobEndpoint=https://***.blob.core.windows.net/;QueueEndpoint=https://***.queue.core.windows.net/;TableEndpoint=https://***.table.core.windows.net/;FileEndpoint=https://myiotservicestorage.file.core.windows.net/;"
container_name="raspberrypic"
blob_name="capture"
# Set the size of the image (in pixels)
img_width = 1280
img_height = 720

INTERVAL = 5
# Initialize GPIO
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.cleanup()
# Read data using pin GPIO17
dhtDevice = dht11.DHT11(pin=17)
#PIR
GPIO.setup(4, GPIO.IN) 

def create_client():

    # Create instance of the device client
    iothub_client = IoTHubDeviceClient.create_from_connection_string(IoTHub_CONNECTION_STRING)
    # Create Azure Blob Storage client
    blob_client = BlobClient.from_connection_string(storage_conn_str, container_name, blob_name)
    image_content_setting = ContentSettings(content_type='image/jpeg')    
    # OpenCV camera
    camera = cv2.VideoCapture(0)
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, img_width)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, img_height)
    # Define a method request handler
    def method_request_handler(method_request):
        if method_request.name == "SetTelemetryInterval":
            try:
                global INTERVAL
                INTERVAL = int(method_request.payload)
                print("Change data collecting Interval to {}".format(INTERVAL))
            except ValueError:
                response_payload = {"Response": "Invalid parameter"}
                response_status = 400
            else:
                response_payload = {"Response": "Executed direct method {}".format(method_request.name)}
                response_status = 200
        elif method_request.name == "CaptureImage":
            try:
                ret, image = camera.read()
                cv2.imwrite('capture.jpg', image)
                # show local image file
                img = cv2.imread('capture.jpg') 
                cv2.imshow('capture',img)
                cv2.waitKey(2000)
                cv2.destroyAllWindows()
                with open("capture.jpg", "rb") as data:
                    blob_client.upload_blob(data,overwrite=True,content_settings=image_content_setting)
                    print("Image Upload completed")                
            except ValueError:
                response_payload = {"Response": "Invalid parameter"}
                response_status = 400
            else:
                response_payload = {"Response": "Executed direct method {}".format(method_request.name)}
                response_status = 200               
        else:
            response_payload = {"Response": "Direct method {} not defined".format(method_request.name)}
            response_status = 404

        method_response = MethodResponse.create_from_method_request(method_request, response_status, response_payload)
        iothub_client.send_method_response(method_response)

    try:
        # Attach the method request handler
        iothub_client.on_method_request_received = method_request_handler
    except:
        # Clean up in the event of failure
        iothub_client.shutdown()
        raise

    return iothub_client

async def run_telemetry_sample(client):
    # This sample will send temperature telemetry every second
    print("IoT Hub device sending periodic messages")

    client.connect()

    while True:
        #DHT11
        result = dhtDevice.read()
        #PIR
        if GPIO.input(4):
            pir = 1
        else:
            pir = 0
            
        if result.is_valid():
            temperature = result.temperature
            humidity = result.humidity
            data = PAYLOAD.format(temperature=temperature, humidity=humidity, pir=pir)
            message = Message(data)

            # Add a custom application property to the message.
            # An IoT hub can filter on these properties without access to the message body.
            if temperature > 30:
                message.custom_properties["temperatureAlert"] = "true"
            else:
                message.custom_properties["temperatureAlert"] = "false"
            # Send a message to the IoT hub
            print(f"Sending message: {message}")
            client.send_message(message)
            print("Message successfully sent")
        else:
            # print("Error: %d" % result.error_code)
            continue

        time.sleep(INTERVAL)
        
async def main():

    print("Device application started. Press Ctrl-C to exit")
    iothub_client = create_client()
    # send telemetry
    try:
        await run_telemetry_sample(iothub_client)
    except KeyboardInterrupt:
        print("IoTHubClient sample stopped by user")
    finally:
        # Upon application exit, shut down the client
        print("Shutting down IoTHubClient")
        iothub_client.shutdown()
        GPIO.cleanup()
    
if __name__ == '__main__':
    asyncio.run(main())