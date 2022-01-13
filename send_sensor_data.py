import asyncio
import time
import board
import RPi.GPIO as GPIO
import dht11
from gpiozero import MotionSensor 
from azure.iot.device import Message
from azure.iot.device.aio import IoTHubDeviceClient

CONNECTION_STRING = "HostName=***.azure-devices.net;DeviceId=***;SharedAccessKey=i598CK6++***"

DELAY = 5
TEMPERATURE = 20.0
HUMIDITY = 60
PAYLOAD = '{{"temperature": {temperature}, "humidity": {humidity}, "PIR": {pir}}}'

async def main():

    try:
        # Create instance of the device client
        client = IoTHubDeviceClient.create_from_connection_string(CONNECTION_STRING)

        # Initialize GPIO
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        GPIO.cleanup()

        # Read data using pin GPIO17
        dhtDevice = dht11.DHT11(pin=17)
        
        GPIO.setup(4, GPIO.IN) #PIR

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

                    data = PAYLOAD.format(temperature=temperature, humidity=humidity, pir=pir)
                    message = Message(data)

                    # Send a message to the IoT hub
                    print(f"Sending message: {message}")
                    await client.send_message(message)
                    print("Message successfully sent")
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
