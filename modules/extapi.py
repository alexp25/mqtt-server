
import time
from modules.constants import Constants
from threading import Thread
from multiprocessing import Queue
from modules.database import Database
import time
from modules.utils import Utils
from modules.classes import Sensor
import requests
import math
from modules.classes import MQTTMessage
from datetime import datetime
from modules.utils import Utils, Singleton
from modules.logg import Logg
import json

@Singleton
class ExtApi(Thread):
    def __init__(self):
        Thread.__init__(self)
        # the actual write to db sampling time
        self.default_log_rate = 1800
        self.logg = Logg.instance()
        self.logstart = False

    def connect(self):
        self.ext_apis = Constants.conf["ENV"]["EXT_API"]
        self.logstart = Constants.conf["ENV"]["EXT_API_LOG_INIT"]
        print(self.ext_apis)
        self.db = Database.instance()
        sensors = self.db.get_sensors()
        print(sensors)
        if sensors is not None:
            self.check_create_sensors(sensors)
        
        # use highest default sampling time from available sensors
        for s in sensors:
            if s["log_rate"] < self.default_log_rate:
                self.default_log_rate = s["log_rate"]

    def check_create_sensors(self, db):
        for e in self.ext_apis:
            if e["ENABLED"]:
                sd = e["SENSOR"]
                exists = False
                for dbs in db:
                    if dbs["sensor_id"] == sd["FULL_ID"]:
                        exists = True
                        break
                if not exists:
                    s = self.create_sensor_model(sd["ID"], sd["TYPE"], sd["LOG_RATE"], sd["TOPIC"], None)
                    # print("newtopic: " + s.topic)
                    self.logg.log("created ext sensor: " + str(s.id))
                    self.create_sensor(s)
                else:
                    self.logg.log("created ext sensor exists: " + str(sd["ID"]))


    def request_data(self):
        for e in self.ext_apis:
            if e["ENABLED"]:
                # api-endpoint
                URL = e['ENDPOINT']
                PARAMS = {}
                HEADERS = {}

                if 'PARAMS' in e:
                    for p in e["PARAMS"]:
                        PARAMS[p['KEY']] = p['VALUE']

                if 'HEADERS' in e:
                    for h in e["HEADERS"]:
                        HEADERS[h['KEY']] = h['VALUE']

                # sending get request and saving the response as response object
                r = requests.get(url=URL, params=PARAMS, headers=HEADERS)

                # extracting data in json format
                data = r.json()

                # print(data)
                self.logg.log(json.dumps(data))

                out = []
                for o in e["OUTPUT"]:

                    d = data

                    for k in o['KEY']:
                        # if isinstance(k, int):
                        d = d[k]
                    out.append(d)

                if 'DERIVATE' in e:
                    for dv in e["DERIVATE"]:
                        d = out[dv['SRC']]
                        # print(d, dv)
                        if 'LIN' in dv:
                            lin = dv['LIN']
                            # print(lin[0], lin[1])
                            d = d * lin[0] + lin[1]
                        if dv['GTZ']:
                            if d < 0:
                                d = 0
                        if dv['FLOOR']:
                            d = math.floor(d)
                        out.append(d)

                self.logg.log(out)

                sd = e["SENSOR"]
                s = self.create_sensor_model(sd["FULL_ID"], sd["TYPE"], sd["LOG_RATE"], sd["TOPIC"], None)

                recv = self.create_message_model(out)

                s.current_data = recv
                s.data_buffer = [recv]
                s.raw_id = sd["ID"]

                if Constants.conf["ENV"]["ENABLE_DB"]:
                    self.db.publish_sensor_data(s)

    def create_sensor(self, sensor):
        if Constants.conf["ENV"]["ENABLE_DB"]:
            return self.db.create_sensor(sensor)
        else:
            return None

    def create_sensor_model(self, id, type, log_rate, topic, data):
        s1 = Sensor()
        s1.current_data = data
        s1.id = id
        s1.type = type
        s1.log_rate = log_rate
        s1.ts = datetime.now()
        s1.topic_name = topic
        s1.log_ts = datetime.now()
        return s1

    def create_message_model(self, data):
        msg = MQTTMessage()
        msg.data = data
        msg.ts = datetime.now()
        return msg

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
                    # self.log_sensor_data()

            except:
                Utils.print_exception(self.__class__.__name__)


if __name__ == '__main__':
    Constants.load()
    Utils.log("config loaded")
    db = Database.instance()
    test = ExtApi.instance()
    print("requesting data")
    test.connect()
    test.request_data()