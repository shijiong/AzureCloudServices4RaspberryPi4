from azure.storage.blob import ContentSettings, BlobClient

import os
from PIL import Image
import matplotlib.pyplot as plt

conn_str="DefaultEndpointsProtocol=https;AccountName=***;AccountKey=***;BlobEndpoint=https://***.blob.core.windows.net/;QueueEndpoint=https://***.queue.core.windows.net/;TableEndpoint=https://***.table.core.windows.net/;FileEndpoint=https://***.file.core.windows.net/;"
container_name="***"
blob_name="capture"

def main():

    print("===== Taking an image - camera =====")
    # capture the image with USB webcamera
    a=os.system("fswebcam --no-banner -r 1280x720 capture.jpg")
    print(a)
    # upload the image to Azure Blob Storage, Overwrite if it already exists!
    blob = BlobClient.from_connection_string(conn_str, container_name, blob_name)
    image_content_setting = ContentSettings(content_type='image/jpeg')
    with open("capture.jpg", "rb") as data:
        blob.upload_blob(data,overwrite=True,content_settings=image_content_setting)
        print("Upload completed")
    # show captured image
    de=Image.open("capture.jpg")
    plt.figure("Result")
    plt.imshow(de)
    plt.show()
    
if __name__ == '__main__':
    main()