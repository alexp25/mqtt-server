import paho.mqtt.client as mqttClient
import paho.mqtt as mqtt
import time
from constants import Constants

class MQTTClient:
    def __init__(self):
        # broker_address = "192.168.12.1"
        # broker_address="iot.eclipse.org" #use external broker
        # self.broker_address = "127.0.0.1"
        self.broker_address = Constants.MQTT_BROKER
        self.client = None

    def disconnect(self):
        if self.client:
            self.client.loop_stop()

    def ping(self, data):
        if Constants.MQTT_PING_TOPIC is not None:
            self.client.publish(Constants.MQTT_PING_TOPIC, payload=data, qos=0, retain=False)

    def connect(self):
        def on_message(client, userdata, message):
            print("message received, topic: ", message.topic, ", message: ", str(message.payload.decode("utf-8")))
            # print("client: ", client)
            # print("message topic =", message.topic)
            # print("message qos =", message.qos)
            # print("message retain flag =", message.retain)

        print("creating new instance")

        self.client = mqttClient.Client(client_id="pc", clean_session=True, userdata=None,
                                   protocol=mqtt.client.MQTTv311, transport="tcp")

        self.client.username_pw_set("60c42070", "87bc58e655e88d7f")
        self.client.on_message = on_message  # attach function to callback

        print("connecting to broker")
        self.client.connect(self.broker_address, port=1883, keepalive=60, bind_address="")

        self.client.loop_start()  # start the loop

        print("subscribing to wsn")

        for topic in Constants.MQTT_SUB_TOPICS:
            self.client.subscribe(topic=topic, qos=0)


