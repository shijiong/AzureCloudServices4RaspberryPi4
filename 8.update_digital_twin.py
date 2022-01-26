import asyncio
import board
import RPi.GPIO as GPIO
import dht11
from azure.iot.hub.models import Twin, TwinProperties
from azure.iot.hub import IoTHubRegistryManager

iothub_connection_str = "HostName=***.azure-devices.net;SharedAccessKeyName=iothubowner;SharedAccessKey=***"
device_id = "MyRPi"
DELAY = 5

async def main():

    try:
        # Create IoTHubRegistryManager
        iothub_registry_manager = IoTHubRegistryManager.from_connection_string(iothub_connection_str)

        # Initialize GPIO
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        GPIO.cleanup()

        # Read data using pin GPIO17
        dhtDevice = dht11.DHT11(pin=17)
        
        GPIO.setup(4, GPIO.IN) #PIR

        print("Sending serivce started. Press Ctrl-C to exit")
        # Get device twin
        twin = iothub_registry_manager.get_twin(device_id)
        print(twin)
        print("")

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
                    # Update twin
                    twin_patch = Twin()
                    twin_patch.properties = TwinProperties(desired={"temperature": temperature})
                    updated_twin = iothub_registry_manager.update_twin(device_id, twin_patch)            
                    print("The twin patch has been successfully applied")

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
