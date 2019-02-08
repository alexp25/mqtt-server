
from flask import Flask
from gevent import pywsgi
from geventwebsocket.handler import WebSocketHandler

from mqtt_client import MQTTClient
from mqtt_manager import MQTTManager
from database import Database
from constants import Constants

import json

# tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dist')
# static_folder = "dist"
# app = Flask(__name__,static_folder=static_folder, template_folder=tmpl_dir)
app = Flask(__name__)
app.debug = False

db = None



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

@app.route("/get-data", methods=['GET'])
def test():
    id = request.args.get('id')
    chan = request.args.get('chan')
    limit = request.args.get('limit')
    data = db.get_sensor_data(id, chan, limit)
    return json.dumps(data)

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

    print("server starting")
    server = pywsgi.WSGIServer(('0.0.0.0', 8083), app, handler_class=WebSocketHandler)
    server.serve_forever()