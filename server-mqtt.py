
from gevent import monkey
monkey.patch_all(thread=False)

from flask import Flask, request, send_file
from gevent import pywsgi
from geventwebsocket.handler import WebSocketHandler

from modules.mqtt_client import MQTTClient
from modules.mqtt_manager import MQTTManager
from modules.database import Database
from modules.constants import Constants
from modules.utils import Utils

import io
import json

from modules.graph import Graph, Timeseries

from modules.logg import Logg

from modules.extapi import ExtApi

from flask_cors import CORS

# tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dist')
# static_folder = "dist"
# app = Flask(__name__,static_folder=static_folder, template_folder=tmpl_dir)
app = Flask(__name__)
CORS(app)
app.debug = False

db = None

graph = Graph.instance()
logg = Logg.instance()
extapi = ExtApi.instance()


@app.route("/")
def hello():
    return "Hello World!"


@app.route("/test")
def test():
    data = db.get_sensors()
    return json.dumps(data)


# if request.method == 'POST':
#       user = request.form['nm']
#       return redirect(url_for('success',name = user))
#    else:
#       user = request.args.get('nm')
#       return redirect(url_for('success',name = user))

@app.route("/get-sensors", methods=['GET'])
def get_sensors():
    try:
        data = db.get_sensors()
        return json.dumps(data)
    except:
        logg.log(Utils.format_exception(""))
        return json.dumps({
            "status": False
        })


@app.route("/get-sensor-data", methods=['GET'])
def get_sensor_data():
    try:
        id = request.args.get('id')
        chan = request.args.get('chan')
        limit = request.args.get('limit')
        data = db.get_sensor_data(id, chan, limit)
        return json.dumps(data, indent=4, sort_keys=True, default=str)
    except:
        logg.log(Utils.format_exception(""))
        return json.dumps({
            "status": False
        })


@app.route("/get-sensor-data-csv", methods=['GET'])
def get_sensor_data_csv():
    try:
        id = request.args.get('id')
        chan = request.args.get('chan')
        limit = request.args.get('limit')
        file = request.args.get('file')
        data = db.get_sensor_data(id, chan, limit)
        # create a dynamic csv or file here using `StringIO`
        # (instead of writing to the file system)

        Utils.log(data)
        strIO = io.BytesIO()

        strdata = db.extract_csv_multichan(data)
        strIO.write(strdata.encode("utf-8"))

        # strIO.write(data)
        strIO.seek(0)

        if file:
            return send_file(strIO,
                             mimetype='text/csv',
                             attachment_filename='downloadFile.csv',
                             as_attachment=True)
        else:
            # assume bytes_io is a `BytesIO` object
            byte_str = strIO.read()

            # Convert to a "unicode" object
            # Or use the encoding you expect
            text_obj = byte_str.decode('UTF-8')

            return json.dumps({
                "status": True,
                "data": text_obj
            })
    except:
        logg.log(Utils.format_exception(""))
        return json.dumps({
            "status": False
        })


@app.route("/get-sensor-data-plot", methods=['GET'])
def get_sensor_data_plot():
    try:
        id = request.args.get('id')
        chan = request.args.get('chan')
        limit = request.args.get('limit')
        data = db.get_sensor_data(id, chan, limit)
        # Utils.log(data)

        if not chan:
            timeseries = []
            for i in range(len(data)):
                timeseries1 = Timeseries()
                timeseries1.x = []
                timeseries1.y = []

                for (i, row) in enumerate(data):
                    timeseries1.x.append(row["timestamp"])
                    timeseries1.y.append(row["value"])

                timeseries.append(timeseries1)

            strIO = graph.plot_timeseries_multi(
                timeseries, "sensor " + id, "time", "value")
        else:
            timeseries = Timeseries()
            timeseries.x = []
            timeseries.y = []
            for (i, row) in enumerate(data):
                timeseries.x.append(row["timestamp"])
                timeseries.y.append(row["value"])
            strIO = graph.plot_timeseries(
                timeseries, "sensor " + id + " chan " + chan, "time", "value")

        return strIO
        # Utils.log(strIO)
        # # attachment_filename = 'plot.png',
        # # as_attachment = True
        # return send_file(strIO,
        #                  mimetype='image/jpg',
        #                  attachment_filename='logo.png',
        #                  )
    except:
        logg.log(Utils.format_exception(""))
        return json.dumps({
            "status": False
        })


if __name__ == '__main__':

    Constants.load()
    Utils.log("config loaded")

    logg = Logg.instance()
    logg.start()

    mqtt_manager = MQTTManager()

    mqtt_manager.create_client()
    mqtt_manager.start()

    if Constants.conf["ENV"]["ENABLE_DB"]:
        Utils.log("enable db")
        db = Database.instance()
        # db.connect()
        mqtt_manager.load_sensors()
        db.run_process()

    extapi.connect()
    extapi.start()

    port = Constants.conf["ENV"]["PORT"]

    Utils.log("server starting on port " + str(port))
    server = pywsgi.WSGIServer(
        ('0.0.0.0', port), app, handler_class=WebSocketHandler)
    server.serve_forever()
