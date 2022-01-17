from azure.cognitiveservices.vision.customvision.prediction import CustomVisionPredictionClient
from msrest.authentication import ApiKeyCredentials
from azure.storage.blob import ContentSettings, BlobClient
from azure.iot.device import Message
from azure.iot.device.aio import IoTHubDeviceClient

import os
from PIL import Image
from PIL import ImageDraw
import matplotlib.pyplot as plt
import asyncio

# custom vision api
credentials = ApiKeyCredentials(in_headers={"Prediction-key": "Your Key"})
predictor = CustomVisionPredictionClient("https://***.cognitiveservices.azure.com/", credentials)
projectID = "******"
publish_iteration_name="Iteration*"

#Bolb Storage
conn_str="DefaultEndpointsProtocol=https;AccountName=***;AccountKey=***;BlobEndpoint=https://***.blob.core.windows.net/;QueueEndpoint=https://***.queue.core.windows.net/;TableEndpoint=https://***.table.core.windows.net/;FileEndpoint=https://***.file.core.windows.net/;"
container_name="raspberrypic"
blob_name="bird"
# Create instance of the device client
blob_client = BlobClient.from_connection_string(conn_str, container_name, blob_name)

# Azure IotHub
CONNECTION_STRING = "HostName=***.azure-devices.net;DeviceId=***;SharedAccessKey=***"
# Create instance of the device client
iothub_client = IoTHubDeviceClient.create_from_connection_string(CONNECTION_STRING)
target_num = 0
PAYLOAD = '{{"No. of target detected": {target_num}}}'

async def CustomVisionApp():

    print("===== Describe an image - camera =====")
    # capture the image with USB webcamera
    a=os.system("fswebcam --no-banner -r 1280x720 capture.jpg")
    print(a)
    # open and detect the captured image
    with open("capture.jpg", mode="rb") as captured_image:
        results = predictor.detect_image(projectID, publish_iteration_name, captured_image)    
    # Display the results.
    for prediction in results.predictions:
        global target_num
        if prediction.probability>0.6:
            target_num += 1
            print("\t" + prediction.tag_name + ": {0:.2f}%".format(prediction.probability * 100))
            bbox = prediction.bounding_box
            im = Image.open("capture.jpg")
            draw = ImageDraw.Draw(im)
            draw.rectangle([int(bbox.left * 1280), int(bbox.top * 720), int((bbox.left + bbox.width) * 1280), int((bbox.top + bbox.height) * 720)],outline='red',width=5)
            im.save("detect.jpg")
    de=Image.open("detect.jpg")
    plt.figure("Result")
    plt.imshow(de)
    plt.show()
    
    #data formating
    data = PAYLOAD.format(target_num=target_num)
    message = Message(data)
    # Send a message to the IoT hub
    print(f"Sending message: {message}")
    await iothub_client.send_message(message)
    print("Message successfully sent")
     
    # upload the image to Azure Blob Storage, Overwrite if it already exists!
    image_content_setting = ContentSettings(content_type='image/jpeg')
    with open("detect.jpg", "rb") as data:
        blob_client.upload_blob(data,overwrite=True,content_settings=image_content_setting)
        print("Upload completed")
    
if __name__ == '__main__':
    asyncio.run(CustomVisionApp())