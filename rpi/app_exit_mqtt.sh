#export pid=`ps aux | grep python | grep hello_gevent.py | awk 'NR==1{print $2}' | cut -d' ' -f1`;kill -9 $pid

for KILLPID in `ps aux | grep 'python' | grep 'server-mqtt' | awk ' { print $2;}'`; do 
  kill -9 $KILLPID;
done


#ps aux | grep python | grep -v grep | awk '{print $2}' | xargs kill -9
