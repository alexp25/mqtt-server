
from flask import Flask, request, send_file
from gevent import pywsgi
from geventwebsocket.handler import WebSocketHandler

from mqtt_client import MQTTClient
from mqtt_manager import MQTTManager
from database import Database
from constants import Constants
from utils import Utils

import io
import json

from graph import Graph, Timeseries

# tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dist')
# static_folder = "dist"
# app = Flask(__name__,static_folder=static_folder, template_folder=tmpl_dir)
app = Flask(__name__)
app.debug = False

db = None

graph = Graph.instance()


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
        Utils.print_exception("")
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
        Utils.print_exception("")
        return json.dumps({
            "status": False
        })

@app.route("/get-sensor-data-csv", methods=['GET'])
def get_sensor_data_csv():
    try:
        id = request.args.get('id')
        chan = request.args.get('chan')
        limit = request.args.get('limit')
        data = db.get_sensor_data(id, chan, limit)
        # create a dynamic csv or file here using `StringIO`
        # (instead of writing to the file system)

        print(data)
        strIO = io.BytesIO()

        # .encode("utf-8")
        timeseries = Timeseries()
        for (i, row) in enumerate(data):
            strIO.write((str(i+1) + "\t" + str(row["value"])  + "\t" + str(row["timestamp"]) + "\n").encode("utf-8"))
            timeseries.x.append(row["timestamp"])
            timeseries.y.append(row["value"])
        graph.plot_timeseries(timeseries, "sensor " + id + " chan " + chan, "time", "value")

        # strIO.write(data)
        strIO.seek(0)
        return send_file(strIO,
                         mimetype='text/csv',
                         attachment_filename='downloadFile.csv',
                         as_attachment=True)
    except:
        Utils.print_exception("")
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
        timeseries = Timeseries()
        for (i, row) in enumerate(data):
            timeseries.x.append(row["timestamp"])
            timeseries.y.append(row["value"])
        html = graph.plot_timeseries(timeseries, "sensor " + id + " chan " + chan, "time", "value")
        return html
    except:
        Utils.print_exception("")
        return json.dumps({
            "status": False
        })





if __name__ == '__main__':

    Constants.load()
    print("config loaded")

    mqtt_manager = MQTTManager()

    mqtt_manager.create_client()
    mqtt_manager.start()

    if Constants.conf["ENABLE_DB"]:
        print("enable db")
        db = Database.instance()
        db.connect()
        mqtt_manager.load_sensors()

    port = 8083
    print("server starting on port " + str(port))
    server = pywsgi.WSGIServer(('0.0.0.0', port), app, handler_class=WebSocketHandler)
    server.serve_forever()