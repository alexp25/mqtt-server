
import time
from constants import Constants
from threading import Thread
from multiprocessing import Queue
from database import Database
import time
from utils import Utils
from classes import Sensor
import requests
import math
from classes import MQTTMessage
from datetime import datetime
from utils import Utils, Singleton
from logg import Logg

@Singleton
class ExtApi(Thread):
    def __init__(self):
        Thread.__init__(self)
        # the actual write to db sampling time
        self.default_log_rate = 3600
        self.aqi = 0
        self.aqius = 0
        self.sid = 3001
        self.stype = 3
        self.logg = Logg.instance()
        self.logstart = False

    def connect(self):
        self.db = Database.instance()
        self.sensors = []
        sensors = self.db.get_sensors()
        t_create = time.time()
        exists = False

        if sensors is not None:
            for s in sensors:
                print(s)
                s1 = Sensor()

                s1.id = s["sensor_id"]
                s1.n_channel = s["n_chan"]
                s1.log_rate = s["log_rate"]
                s1.flag1 = s["flag1"]
                s1.topic_code = s["topic_code"]
                s1.type = s["sensor_type_code"]
                s1.ts = t_create
                s1.log_ts = t_create

                if s1.id == self.sid:
                    exists = True
                self.sensors.append(s1)

        if not exists:
            self.create_sensor(self.create_sensor_model(None))
            self.logg.log("created ext sensor")
        else:
            self.logg.log("ext sensor exists")


    def request_data(self):

        # api-endpoint
        URL = "http://api.airvisual.com/v2/nearest_city"


        # defining a params dict for the parameters to be sent to the API
        PARAMS = {'lat': 44.4567471,
                  'lon': 26.080335,
                  'key': 'kFHKw8oi3K56wzRhN'}

        # sending get request and saving the response as response object
        r = requests.get(url=URL, params=PARAMS)

        # extracting data in json format
        data = r.json()

        self.aqius = data["data"]["current"]["pollution"]["aqius"]

        self.aqi = (self.aqius * 0.6613 - 10.07)
        self.aqi = math.floor(self.aqi)
        if self.aqi < 0:
            self.aqi = 0

    def create_sensor(self, sensor):
        if Constants.conf["ENV"]["ENABLE_DB"]:
            return self.db.create_sensor(sensor)
        else:
            return None

    def create_sensor_model(self, data):
        s1 = Sensor()
        s1.current_data = data
        s1.id = self.sid
        s1.n_channel = 2
        s1.type = self.stype
        s1.log_rate = self.default_log_rate
        s1.ts = datetime.now()
        s1.flag1 = False
        s1.log_ts = datetime.now()
        return s1

    def create_message_model(self, data):
        msg = MQTTMessage()
        msg.data = data
        msg.ts = datetime.now()
        return msg

    def log_sensor_data(self):
        s1 = self.create_sensor_model(None)
        recv = self.create_message_model([self.aqius, self.aqi])
        s1.data_buffer = [recv]
        if Constants.conf["ENV"]["ENABLE_DB"]:
            self.db.publish_sensor_data(sensor=s1)

    def run(self):
        t0 = time.time()
        while True:
            time.sleep(Constants.LOOP_DELAY)
            t1 = time.time()
            try:
                if (t1 - t0) >= self.default_log_rate or self.logstart:
                    self.logstart = False
                    t0 = t1
                    self.logg.log("Requesting ext api")
                    self.request_data()
                    self.log_sensor_data()

            except:
                Utils.print_exception(self.__class__.__name__)


if __name__ == '__main__':
    test = ExtApi()
    print("requesting data")
    # test.request_data()