import paho.mqtt.client as mqttClient
import paho.mqtt as mqtt
import time
from constants import Constants
from multiprocessing import Queue
from utils import Utils
from datetime import datetime
from classes import MQTTMessage
from logg import Logg

class MQTTClient:
    def __init__(self):
        # broker_address = "192.168.12.1"
        # broker_address="iot.eclipse.org" #use external broker
        # self.broker_address = "127.0.0.1"
        self.broker_address = Constants.conf["ENV"]["MQTT_BROKER"]
        self.client = None
        self.sensor_data_q = Queue()
        self.connected = False
        self.logg = Logg.instance()

    def get_data_q(self):
        return self.sensor_data_q

    def disconnect(self):
        if self.client:
            self.client.loop_stop()

    def ping(self, data):
        if Constants.conf["ENV"]["MQTT_PING_TOPIC"] is not None:
            self.client.publish(Constants.conf["ENV"]["MQTT_PING_TOPIC"], payload=data, qos=0, retain=False)

    def connect(self):
        def on_connect(client, userdata, flags, rc):
            self.logg.log("client: " + str(client) + " connected")
            self.connected = True

        def on_disconnect(client, userdata, rc):
            self.logg.log("client: " + str(client) + " disconnected")
            self.connected = False
            try:
                if self.client:
                    self.client.loop_stop()
            except:
                self.logg.log(Utils.format_exception(self.__class__.__name__))

        def on_message(client, userdata, message):
            try:
                # self.logg.log("message received, topic: ", message.topic, ", message: ", str(message.payload.decode("utf-8")))
                # self.logg.log("client: ", client)
                # self.logg.log("message topic =", message.topic)
                # self.logg.log("message qos =", message.qos)
                # self.logg.log("message retain flag =", message.retain)

                raw_data = str(message.payload.decode("utf-8"))
                msg = MQTTMessage()

                topic_elems = message.topic.split("/")
                n_topic_elems = len(topic_elems)

                msg.data = raw_data.split(",")

                msg.topic = "/".join(topic_elems[0:n_topic_elems-2])
                # self.logg.log(msg.topic)

                # the last-1 item is the sensor id
                # the last item is the input/output selector (cmd, sns)

                msg.id = int(topic_elems[n_topic_elems-2])
                msg.ts = datetime.now()
                # fixed type at the moment
                msg.type = 1

                # TODO: use a different topic for each sensor type, e.g. wsn/indoor, wsn/outdoor
                # TODO: only log the known sensors in the db and filter them by the topic ID

                if not self.sensor_data_q.full():
                    self.sensor_data_q.put(msg)
            except:
                self.logg.log(Utils.format_exception(self.__class__.__name__))

        self.logg.log("creating new instance")

        self.client = mqttClient.Client(client_id="pc", clean_session=True, userdata=None,
                                   protocol=mqtt.client.MQTTv311, transport="tcp")

        self.client.username_pw_set("60c42070", "87bc58e655e88d7f")
        self.client.on_message = on_message  # attach function to callback
        self.client.on_connect = on_connect
        self.client.on_disconnect = on_disconnect

        self.logg.log("connecting to broker")
        self.client.connect(self.broker_address, port=1883, keepalive=60, bind_address="")

        self.client.loop_start()  # start the loop

        self.logg.log("subscribing to wsn")

        for topic in Constants.conf["ENV"]["MQTT_SUB_TOPICS"]:
            self.client.subscribe(topic=topic, qos=0)


