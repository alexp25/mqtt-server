import time
from constants import Constants
from mqtt_client import MQTTClient, MQTTMessage
from threading import Thread
from multiprocessing import Queue
from database import Database
import time
from utils import Utils
from classes import Sensor
import json
import datetime
from logg import Logg


class MQTTManager(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.mqtt_client = None
        self.sensor_data_q = None
        self.sensors = []
        # the actual write to db sampling time
        self.default_log_rate = 20
        # the sampling time of the sensor (it may send data faster than this, so just ignore the data in between)
        self.default_min_sampling_rate = 10
        self.logg = Logg.instance()

    def create_client(self):
        self.mqtt_client = MQTTClient()
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
                    s1 = Sensor()
                    s1.id = s["sensor_id"]
                    s1.n_channel = s["n_chan"]
                    s1.log_rate = s["log_rate"]
                    s1.flag1 = s["flag1"]
                    s1.topic_code = s["topic_code"]
                    s1.type = s["sensor_type_code"]
                    s1.ts = t_create
                    s1.log_ts = t_create

                    # self.logg.log(json.dumps(s1.__dict__))

                    self.sensors.append(s1)
            self.logg.log(self.sensors)
        except:
            self.logg.log(Utils.format_exception(self.__class__.__name__))

    def update_sensor_data(self, id, data):
        ts = time.time()
        found = False
        s1 = Sensor()
        s1_update = None
        d1 = MQTTMessage(data)

        try:
            for s in self.sensors:
                s1 = Sensor(s)
                s1_update = s
                if s1.id == Utils.get_sensor_id_encoding(id, s1.topic_code):
                    found = True
                    # self.logg.log("found")
                    break
            if found:
                # for real time monitor
                if s1.flag1 and data.data[0] != "data":
                    return

                s1.current_data = data

                # handle sample and db log
                if ts - s1.ts >= s1.log_rate:
                    # self.logg.log("sample")
                    s1_update.ts = ts
                    s1.data_buffer.append(data)

                if ts - s1.log_ts >= self.default_log_rate:
                    # self.logg.log("log")
                    s1_update.log_ts = ts
                    if len(s1.data_buffer) > 0:
                        self.log_sensor_data(s1)
                        s1_update.data_buffer = []
            else:
                # sensor is not defined in the db, save and use defaults
                # assign to the topic (should be defined)
                self.logg.log("create sensor")
                s1.current_data = data
                s1.id = id
                s1.n_channel = len(d1.data)
                s1.type = d1.type
                s1.log_rate = self.default_log_rate
                s1.ts = ts
                s1.log_ts = ts
                # write to db
                s1 = self.create_sensor(s1)
                if s1 is not None:
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
            self.db.publish_sensor_data(sensor=s)

    def run(self):
        t0 = time.time()
        while True:
            time.sleep(Constants.LOOP_DELAY)
            t1 = time.time()
            try:

                if (t1 - t0) >= 10:
                    t0 = t1
                    self.logg.log("self test")
                    if not self.mqtt_client.connected:
                        self.logg.log("disconnect detected, reconnect")
                        self.mqtt_client.connect()
                    self.mqtt_client.ping("self test")


                if not self.sensor_data_q.empty():
                    recv = MQTTMessage(self.sensor_data_q.get(block=False))
                    self.update_sensor_data(recv.id, recv)
                    if Constants.conf["ENV"]["LOG_SENSOR_DATA"]:
                        self.logg.log(recv.topic + " " + str(recv.id) + " " + str(recv.data))

            except:
                self.logg.log(Utils.format_exception(self.__class__.__name__))


