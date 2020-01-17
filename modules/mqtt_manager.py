import time
from modules.constants import Constants
from modules.mqtt_client import MQTTClient, MQTTMessage
from threading import Thread
from multiprocessing import Queue
from modules.database import Database
import time
from modules.utils import Utils
from modules.classes import Sensor
import json
import datetime
from modules.logg import Logg
from typing import List
from modules.classes import MQTTTopic
import copy


class MQTTManager(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.mqtt_client = None
        self.sensor_data_q = None
        self.sensors: List[Sensor] = []

        self.topics: List[MQTTTopic] = []

        # the actual write to db sampling time
        self.default_log_rate = 20
        # the sampling time of the sensor (it may send data faster than this, so just ignore the data in between)
        self.default_min_sampling_rate = 10
        self.logg = Logg.instance()

    def create_client(self):
        self.mqtt_client = MQTTClient()
        self.mqtt_client.setup()
        self.mqtt_client.connect()
        self.sensor_data_q = self.mqtt_client.get_data_q()

    def load_sensors(self):
        self.logg.log("load sensors")
        try:
            self.db = Database.instance()
            sensors = self.db.get_sensors()
            self.logg.log(sensors)
            t_create = time.time()
            if sensors is not None:
                for s in sensors:
                    s1: Sensor = Sensor()
                    s1.id = s["sensor_id"]
                    s1.log_rate = s["log_rate"]
                    s1.topic_name = s["topic_name"]
                    s1.topic_code = s["topic_code"]
                    s1.type = s["sensor_type_code"]
                    s1.ts = t_create
                    s1.log_ts = t_create
                    # self.logg.log(json.dumps(s1.__dict__))
                    self.sensors.append(s1)

            topics = self.db.get_topics()

            if topics is not None:
                for t in topics:
                    t1: MQTTTopic = MQTTTopic(t)
                    self.topics.append(t1)

            self.logg.log(self.topics)
            self.logg.log(self.sensors)
        except:
            self.logg.log(Utils.format_exception(self.__class__.__name__))

    def get_topic_code(self, topic_name):
        for t in self.topics:
            if t.name == topic_name:
                return t.code
        return None

    def update_sensor_data(self, raw_id, d1: MQTTMessage):
        ts = time.time()
        found = False
        s1: Sensor = Sensor()

        # remove heading
        data = d1.data
        if d1.data[0] == "data":
            data = d1.data[1:]

        d1.data = data

        try:
            for s in self.sensors:
                s1 = s
                if s1.id == Utils.get_sensor_id_encoding(raw_id, self.get_topic_code(d1.topic)):
                    found = True
                    # self.logg.log("found / " + d1.topic + ": " + str(s1.id) + " raw id: " + str(raw_id) + " topic code: " + str(s1.topic_code))
                    break

            if found:
                # print(d1)
                # for real time monitor
                # self.logg.log("update sensor/" + d1.topic)

                s1.current_data = data

                # handle sample and db log
                if ts - s1.ts >= s1.log_rate:
                    # self.logg.log("sample")
                    s1.ts = ts
                    s1.data_buffer.append(d1)

                if ts - s1.log_ts >= self.default_log_rate:
                    # self.logg.log("log")
                    s1.log_ts = ts
                    if len(s1.data_buffer) > 0:
                        self.log_sensor_data(s1)
                        s1.data_buffer = []
            else:
                # sensor is not defined in the db, save and use defaults
                # assign to the topic (should be defined)
                self.logg.log("create sensor")
                s1.current_data = d1
                s1.raw_id = raw_id
                s1.type = d1.type
                s1.log_rate = self.default_log_rate
                s1.ts = ts
                s1.log_ts = ts
                s1.topic_name = d1.topic

                # write to db
                s1 = self.create_sensor(s1)

                # topic code is now assigned

                if s1 is not None:
                    self.logg.log("new sensor: " + str(s1.__dict__))
                    self.sensors.append(s1)

        except:
            self.logg.log(Utils.format_exception(self.__class__.__name__))

        # self.logg.log(self.sensors)

    def create_sensor(self, sensor):
        if Constants.conf["ENV"]["ENABLE_DB"]:
            return self.db.create_sensor(sensor)
        else:
            return None

    def log_sensor_data(self, sensor):
        s = Sensor(sensor)
        if Constants.conf["ENV"]["ENABLE_DB"]:
            self.db.publish_sensor_data(copy.deepcopy(s))

    def run(self):
        t0 = time.time()
        while True:
            time.sleep(Constants.LOOP_DELAY)
            t1 = time.time()
            try:

                if (t1 - t0) >= 10:
                    t0 = t1
                    # self.logg.log("self test")
                    if not self.mqtt_client.connected:
                        self.logg.log("disconnect detected, reconnect")
                        try:
                            self.mqtt_client.connect()
                        except:
                            self.logg.log(Utils.format_exception(
                                self.__class__.__name__))
                    self.mqtt_client.ping("self test")

                if not self.sensor_data_q.empty():
                    recv: MQTTMessage = self.sensor_data_q.get(block=False)
                    self.update_sensor_data(recv.id, recv)
                    if Constants.conf["ENV"]["LOG_SENSOR_DATA"]:
                        self.logg.log(recv.topic + " " +
                                      str(recv.id) + " " + str(recv.data))

            except:
                self.logg.log(Utils.format_exception(self.__class__.__name__))
