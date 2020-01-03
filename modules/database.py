
from modules.utils import Utils, Singleton
from modules.classes import MQTTMessage
from modules.classes import Sensor
from modules.constants import Constants

import pymysql.cursors
import pymysql

from modules.logg import Logg

import time

from multiprocessing import Queue, Process


def PublisherProcess(q_in: Queue, q_out: Queue, conf):

    dbconf = conf["ENV"]["DB"]

    host = dbconf["HOST"]
    user = dbconf["USER"]
    password = dbconf["PASS"]
    dbname = dbconf["NAME"]

    connection = pymysql.connect(
        host=host,
        user=user,
        password=password,
        database=dbname,
        cursorclass=pymysql.cursors.DictCursor
    )

    cursor = connection.cursor()
    print("connected to db (process)")

    while True:
        time.sleep(0.01)
        if not q_in.empty():
            s: Sensor = q_in.get()
            publish_sensor_data_ext(s, connection, cursor)


@Singleton
class Database:
    def __init__(self):
        self.connection = None
        self.cursor = None
        self.connected = False
        self.logg = Logg.instance()

        self.dbq_in = Queue()
        self.dbq_out = Queue()

    def run_process(self):
        if not (Constants.conf["ENV"]["USE_EXT_PUBLISHER"] and Constants.conf["ENV"]["USE_PUBLISHER_PROCESS"]):
            return
        p = Process(target=PublisherProcess, args=(
            self.dbq_in, self.dbq_out, Constants.conf))
        p.start()

    def connect(self):
        self.logg.log("connecting to db")
        try:
            dbconf = Constants.conf["ENV"]["DB"]
            host = dbconf["HOST"]
            user = dbconf["USER"]
            password = dbconf["PASS"]
            dbname = dbconf["NAME"]

            # db type e.g. mysql, postgresql
            dbtype = dbconf["TYPE"]

            if dbtype == "MYSQL":
                self.connection = pymysql.connect(
                    host=host,
                    user=user,
                    password=password,
                    database=dbname,
                    cursorclass=pymysql.cursors.DictCursor
                )
                # self.cursor = self.connection.cursor(pymysql.cursors.DictCursor)
                self.cursor = self.connection.cursor()
            else:
                pass

            self.connected = True
            self.logg.log("connected to db")
        except:
            self.logg.log(Utils.format_exception(self.__class__.__name__))

    def check_connect(self):
        if not self.connected:
            self.connect()

    def get_topics(self):
        self.check_connect()

        try:
            self.cursor.execute('select * from topic')
            results = self.cursor.fetchall()
            self.connection.commit()
            return results
        except:
            self.logg.log(Utils.format_exception(self.__class__.__name__))
            return None
        finally:
            self.connection.commit()

    def get_sensors(self):
        self.check_connect()

        try:
            self.cursor.execute(
                'select sensor.sensor_id, sensor.log_rate, sensor.topic_code, sensor.sensor_type_code, topic.name as "topic_name" from sensor inner join topic on sensor.topic_code=topic.code')
            results = self.cursor.fetchall()
            self.connection.commit()
            return results
        except:
            self.logg.log(Utils.format_exception(self.__class__.__name__))
            return None
        finally:
            self.connection.commit()

    def get_sensor_data(self, id, chan, limit):
        self.check_connect()

        try:
            sql = 'select * from (select * from sensor_data where sensor_id=%s and chan=%s order by id DESC limit %s) as data_desc order by data_desc.id ASC'
            params = (int(id), int(chan), int(limit))
            self.logg.log(sql)
            self.logg.log(params)
            self.cursor.execute(sql, params)
            results = self.cursor.fetchall()
            self.connection.commit()
            return results
        except:
            self.logg.log(Utils.format_exception(self.__class__.__name__))
            return None
        finally:
            self.connection.commit()

    def create_sensor(self, sensor):
        self.check_connect()

        try:
            sdata: MQTTMessage = sensor.current_data
            # self.logg.log(sdata.__dict__)
            if not sdata:
                return None

            self.logg.log("create sensor for topic: " + sensor.topic_name +
                          " (code " + str(sensor.topic_code) + ")")
            self.cursor.execute(
                'select * from topic where name=%s', (sensor.topic_name,))
            topic = self.cursor.fetchone()
            self.logg.log(
                "topic[" + str(sensor.topic_name) + "]: " + str(topic))
            # self.logg.log(topic["id"])
            sensor.id = Utils.get_sensor_id_encoding(
                sensor.raw_id, topic["code"])
            sql = "INSERT INTO sensor (sensor_id, log_rate, topic_code) VALUES (%s, %s, %s)"
            sensor.log_rate = topic["log_rate"]
            sensor.topic_code = topic["code"]

            self.logg.log("sensor: " + str(sensor.__dict__))
            params = (sensor.id, sensor.log_rate, topic["code"])
            self.logg.log(sql + str(params))
            self.cursor.execute(sql, params)
            # commit the changes to the database
            self.connection.commit()
            # close communication with the database
            # self.cursor.close()
            return sensor
        except:
            self.logg.log(Utils.format_exception(self.__class__.__name__))
            return None
        finally:
            try:
                self.connection.commit()
            except:
                self.logg.log(Utils.format_exception(self.__class__.__name__))

    def publish_sensor_data_core(self, s: Sensor):
        sql = "INSERT INTO sensor_data(sensor_id, chan, value, timestamp) VALUES(%s, %s, %s, %s)"
        self.logg.log("publish data")

        self.logg.log(s.__dict__)
        publish_sensor_data_ext(s, self.connection, self.cursor)

    def publish_sensor_data(self, s: Sensor):
        if Constants.conf["ENV"]["USE_EXT_PUBLISHER"]:
            if not self.dbq_in.full():
                self.dbq_in.put(s)
        else:
            self.check_connect()
            self.publish_sensor_data_core(s)


def publish_sensor_data_ext(s: Sensor, connection, cursor):
    sql = "INSERT INTO sensor_data(sensor_id, chan, value, timestamp) VALUES(%s, %s, %s, %s)"
    print("publish data ext")
    try:
        insert_list = []

        for msg in s.data_buffer:

            n_data = len(msg.data)
            r = range(0, n_data)

            for index in r:
                try:
                    data_val = int(msg.data[index])
                    insert_list.append((s.id, index, data_val, msg.ts))
                except:
                    # print(Utils.format_exception("publish sensor data ext"))
                    continue

        if len(insert_list) > 0:
            # print(insert_list)
            print(insert_list)
            cursor.executemany(sql, insert_list)
            # close communication with the database
            # cursor.close()
        else:
            print("no data to insert: " + str(len(s.data_buffer)))

    except:
        print(Utils.format_exception("publish sensor data ext"))
    finally:
        try:
            # commit the changes to the database
            connection.commit()
        except:
            print(Utils.format_exception("publish sensor data ext"))
