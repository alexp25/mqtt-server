
from flask import Flask
from gevent import pywsgi
from geventwebsocket.handler import WebSocketHandler

from mqtt_client import MQTTClient
from mqtt_manager import MQTTManager

# tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dist')
# static_folder = "dist"
# app = Flask(__name__,static_folder=static_folder, template_folder=tmpl_dir)
app = Flask(__name__)
app.debug = False


@app.route("/")
def hello():
    return "Hello World!"


if __name__ == '__main__':

    mqttManager = MQTTManager()
    mqttManager.create_client()
    mqttManager.run()

    server = pywsgi.WSGIServer(('0.0.0.0', 8083), app, handler_class=WebSocketHandler)
    server.serve_forever()