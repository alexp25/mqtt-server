import paho.mqtt.client as mqttClient
import paho.mqtt as mqtt
import time

class MQTTClient:
    def __init__(self):
        # broker_address = "192.168.12.1"
        # broker_address="iot.eclipse.org" #use external broker
        # self.broker_address = "127.0.0.1"
        self.broker_address = "192.168.12.160"
        self.client = None

    def disconnect(self):
        if self.client:
            self.client.loop_stop()

    def ping(self, data):
        self.client.publish("wsn/check", payload=data, qos=0, retain=False)

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

        self.client.on_message = on_message  # attach function to callback

        print("connecting to broker")
        self.client.connect(self.broker_address, port=1883, keepalive=60, bind_address="")

        self.client.loop_start()  # start the loop

        print("subscribing to wsn")

        self.client.subscribe("wsn/#")

        print("publishing to wsn/check")
        self.client.publish("wsn/check", payload="test", qos=0, retain=False)


