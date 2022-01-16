import asyncio
import time
import board
import RPi.GPIO as GPIO
import dht11

from datetime import datetime
from uuid import uuid4
from azure.data.tables import TableServiceClient
from azure.data.tables import UpdateMode

#Azure Storage Connection String
Storage_CONNECTION_STRING = "DefaultEndpointsProtocol=https;AccountName=***;AccountKey=***;EndpointSuffix=core.windows.net"

#Delay time, in seconds
DELAY = 5

async def main():

    try:
        # Create instance of the storage client and table client
        table_service_client = TableServiceClient.from_connection_string(Storage_CONNECTION_STRING)
        table_name = "myTable"
        table_client = table_service_client.create_table_if_not_exists(table_name)
        # Initialize GPIO
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        GPIO.cleanup()

        # Read data using pin GPIO17
        dhtDevice = dht11.DHT11(pin=17)
        # PIR
        GPIO.setup(4, GPIO.IN) 

        print("Sending serivce started. Press Ctrl-C to exit")
        while True:

            try:
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

                    my_entity = {
                            u"PartitionKey": u"Raspberry Pi 4",
                            u"RowKey": uuid4(),
                            "temperature": temperature,
                            "humidity": humidity,
                            "PIR": pir,
                            "last_updated": datetime.today()
                        }

                    # START insert entity
                    insert_entity = table_client.upsert_entity(my_entity)
                    print("Inserted entity: {}".format(insert_entity))
               
                else:
                    # print("Error: %d" % result.error_code)
                    continue

                await asyncio.sleep(DELAY)

            except KeyboardInterrupt:
                print("Service stopped")
                GPIO.cleanup()
                break

    except Exception as error:
        print(error.args[0])

if __name__ == '__main__':
    asyncio.run(main())
