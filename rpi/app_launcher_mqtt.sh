#!/bin/sh
# launcher.sh
# navigate to home directory, then to this directory, then execute python script, then back home
#source `which virtualenvwrapper.sh`
#source /path/to/virtualenvwrapper.sh # if it's not in your PATH
#workon cv3
cd /
cd home/pi/Desktop/mqtt-server
#echo type app name [ENTER]: 
#read app
#if [ -n "$app" ]; then
#	echo "starting default"
#	sudo python $app.py	
#else
#	echo "starting app"
#	sudo python hello_gevent.py
#fi
sudo python server-mqtt.py
cd /
#deactivate
