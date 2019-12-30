
from modules.utils import Utils, Singleton
from modules.classes import MQTTMessage
from modules.classes import Sensor
from modules.constants import Constants

import pymysql.cursors
import pymysql

from modules.logg import Logg


@Singleton
class Database:
    def __init__(self):
        self.conn = None
        self.cur = None
        self.connected = False
        self.logg = Logg.instance()

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
                self.conn = pymysql.connect(
                    host=host,
                    user=user,
                    password=password,
                    database=dbname,
                    cursorclass=pymysql.cursors.DictCursor
                )
                # self.cur = self.conn.cursor(pymysql.cursors.DictCursor)
                self.cur = self.conn.cursor()
            else:
                pass        
           
            self.connected = True
            self.logg.log("connected to db")
        except:
            self.logg.log(Utils.format_exception(self.__class__.__name__))

    def check_connect(self):
        if not self.connected:
            self.connect()

    def get_sensors(self):
        self.check_connect()

        try:
            self.cur.execute('select sensor.sensor_id, sensor.log_rate, sensor.topic_code, sensor.sensor_type_code, topic.name as "topic_name" from sensor inner join topic on sensor.topic_code=topic.code')
            results = self.cur.fetchall()
            self.conn.commit()
            return results
        except:
            self.logg.log(Utils.format_exception(self.__class__.__name__))
            return None
        finally:
            self.conn.commit()

    def get_sensor_data(self, id, chan, limit):
        self.check_connect()

        try:
            sql = 'select * from (select * from sensor_data where sensor_id=%s and chan=%s order by id DESC limit %s) as data_desc order by data_desc.id ASC'
            params = (int(id), int(chan), int(limit))
            self.logg.log(sql)
            self.logg.log(params)
            self.cur.execute(sql, params)
            results = self.cur.fetchall()
            self.conn.commit()
            return results
        except:
            self.logg.log(Utils.format_exception(self.__class__.__name__))
            return None
        finally:
            self.conn.commit()

    def create_sensor(self, sensor):
        self.check_connect()

        try:
            sdata: MQTTMessage = sensor.current_data
            # self.logg.log(sdata.__dict__)
            if not sdata:
                return None

            self.logg.log("create sensor for topic: " + sensor.topic_name + " (code " + str(sensor.topic_code) + ")")
            self.cur.execute('select * from topic where name=%s', (sensor.topic_name,))
            topic = self.cur.fetchone()
            self.logg.log("topic[" + str(sensor.topic_name) + "]: " + str(topic))
            # self.logg.log(topic["id"])
            sensor.id = Utils.get_sensor_id_encoding(sensor.raw_id, topic["code"])
            sql = "INSERT INTO sensor (sensor_id, log_rate, topic_code) VALUES (%s, %s, %s)"
            sensor.log_rate = topic["log_rate"]
            sensor.topic_code = topic["code"]

            self.logg.log("sensor: " + str(sensor.__dict__))
            params = (sensor.id, sensor.log_rate, topic["code"])
            self.logg.log(sql + str(params))
            self.cur.execute(sql, params)
            # commit the changes to the database
            self.conn.commit()
            # close communication with the database
            # self.cur.close()
            return sensor
        except:
            self.logg.log(Utils.format_exception(self.__class__.__name__))
            return None
        finally:
            self.conn.commit()

    def publish_sensor_data(self, s: Sensor):
        self.check_connect()

        sql = "INSERT INTO sensor_data(sensor_id, chan, value, timestamp) VALUES(%s, %s, %s, %s)"
        self.logg.log("publish data")

        self.logg.log(s.__dict__)
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
                        self.logg.log(Utils.format_exception(self.__class__.__name__))
                        continue

            if len(insert_list) > 0:
                # print(insert_list)
                self.logg.log(insert_list)
                self.cur.executemany(sql, insert_list)
                # commit the changes to the database
                self.conn.commit()
                # close communication with the database
                # self.cur.close()
            else:
                self.logg.log("no data to insert: " + str(len(s.data_buffer)))
            
        except:
            self.logg.log(Utils.format_exception(self.__class__.__name__))
        finally:
            self.conn.commit()