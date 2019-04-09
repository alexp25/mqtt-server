import psycopg2
from psycopg2.extras import RealDictCursor
from utils import Utils, Singleton
from classes import MQTTMessage
from classes import Sensor
from constants import Constants

@Singleton
class Database:
    def __init__(self):
        self.conn = None
        self.cur = None

    def connect(self):
        print("connecting to db")
        try:
            dbconf = Constants.conf["DB"]
            dbconf_dev = Constants.conf["DB_DEV"]

            host = dbconf["HOST"]
            user = dbconf["USER"]
            password = dbconf["PASS"]
            dbname = dbconf["NAME"]

            if Constants.conf["DEV"]:
                host = dbconf_dev["HOST"]
                user = dbconf_dev["USER"]
                password = dbconf_dev["PASS"]
                dbname = dbconf_dev["NAME"]

            self.conn = psycopg2.connect(
                host=host,
                user=user,
                password=password,
                dbname=dbname)

            self.cur = self.conn.cursor(cursor_factory=RealDictCursor)
            print("connected to db")
        except:
            Utils.print_exception(self.__class__.__name__)

    def get_sensors(self):
        try:
            self.cur.execute('select sensor.sensor_id, sensor.n_chan, sensor.log_rate, sensor.flag1, sensor.topic_id, sensor.sensor_type_code, topic.name as "topic_name" from sensor inner join topic on sensor.topic_id=topic.id')

            results = self.cur.fetchall()

            return results
        except:
            Utils.print_exception(self.__class__.__name__)
            return None

    def get_sensor_data(self, id, chan, limit):
        try:
            sql = 'select * from (select * from sensor_data where sensor_id=%s and chan=%s order by id DESC limit %s) as data_desc order by data_desc.id ASC'
            self.cur.execute(sql, (id, chan, limit))
            results = self.cur.fetchall()
            return results
        except:
            Utils.print_exception(self.__class__.__name__)
            return None

    def create_sensor(self, sensor):
        try:
            sdata = MQTTMessage(sensor.current_data)
            print(sdata.__dict__)
            if not sdata:
                return None
            self.cur.execute('select * from topic where name=%s', (sdata.topic,))
            topic = self.cur.fetchone()
            print(topic)
            # print(topic["id"])
            sensor.id = Utils.get_sensor_id_encoding(sensor.id, topic["id"])
            sql = "INSERT INTO sensor(sensor_id, n_chan, log_rate, flag1, topic_id) VALUES(%s, %s, %s, %s, %s)"
            sensor.n_channel = topic["n_chan"]
            sensor.log_rate = topic["log_rate"]
            sensor.flag1 = topic["flag1"]
            self.cur.execute(sql, (sensor.id, sensor.n_channel, sensor.log_rate, sensor.flag1, topic["id"]))
            # commit the changes to the database
            self.conn.commit()
            # close communication with the database
            # self.cur.close()
            return sensor
        except:
            Utils.print_exception(self.__class__.__name__)
            return None


    def publish_sensor_data(self, sensor):
        sql = "INSERT INTO sensor_data(sensor_id, chan, value, timestamp) VALUES(%s, %s, %s, %s)"
        print("publish data")
        s = Sensor(sensor)
        print(s.__dict__)
        try:
            insert_list = []
            n_data = s.n_channel
            if s.flag1:
                index_data = range(1, n_data+1)
            else:
                index_data = range(0, n_data)

            for msg in s.data_buffer:
                msg1 = MQTTMessage(msg)
                # for index, d in enumerate(msg1.data):
                #     insert_list.append((sensor_id, index, d))
                # print(msg1.data)
                # insert all data channels that are defined for the sensor type
                for index in index_data:
                    if index < len(msg1.data):
                        insert_list.append((s.id, index, int(msg1.data[index]), msg1.ts))

            # print(insert_list)
            self.cur.executemany(sql, insert_list)
            # commit the changes to the database
            self.conn.commit()
            # close communication with the database
            # self.cur.close()
        except:
            Utils.print_exception(self.__class__.__name__)
