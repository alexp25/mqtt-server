import time
from constants import Constants
from mqtt_client import MQTTClient

class MQTTManager:
    def __init__(self):
        self.mqttClient = None

    def createClient(self):
        self.mqttClient = MQTTClient()
        self.mqttClient.connect()

    def run(self):
        t0 = time.time()
        while True:
            time.sleep(Constants.LOOP_DELAY)
            t1 = time.time()
            if (t1 - t0) >= 10:
                t0 = t1
                self.mqttClient.ping("self test")
