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
            # self.conn = psycopg2.connect(
            #     host='192.168.1.150',
            #     user='pi',
            #     password='raspberry',
            #     dbname='mqtt_charts')

            # self.conn = psycopg2.connect(
            #     host='localhost',
            #     user='pi',
            #     password='raspberry',
            #     dbname='mqtt_charts')

            self.conn = psycopg2.connect(
                host=Constants.conf["DB"]["HOST"],
                user=Constants.conf["DB"]["USER"],
                password=Constants.conf["DB"]["PASS"],
                dbname=Constants.conf["DB"]["NAME"])

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

            sql = 'select * from sensor_data where sensor_id=%s and chan=%s limit %s'
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
