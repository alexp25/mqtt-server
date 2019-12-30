import time
import datetime
from threading import Thread
from modules.utils import Singleton
from multiprocessing import Queue
from modules.utils import Utils


@Singleton
class Logg(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.q = Queue(maxsize=50)
        self.fileindex = 1
        self.folder = "logs"
        self.filename = "log_" + str(int(time.time())) + "_" + str(self.fileindex) +  ".txt"

    def log(self, msg):
        if not self.q.full():
            self.q.put(msg)
        else:
            print("full q")

    def run(self):
        n_max_log = 50
        dt_log = 10
        n_max_lines_file = 100000

        msg = "[Logg] " + "running"
        print(msg)

        first = True
        cnt = 0
        cnt_file = 0

        t1_log = time.time()
        buf = []


        while True:
            time.sleep(0.01)
            t1 = time.time()

            if not self.q.empty():
                dtime = datetime.datetime.now()
                crt_time = dtime.strftime("%H:%M:%S.%f")
                p = crt_time + ': ' + str(self.q.get(block=False))
                print(p)

                p = str(dtime.date()) + ' ' + p

                buf.append(p)
                cnt += 1
                cnt_file += 1

                if (cnt >= n_max_log) or (((t1 - t1_log) >= dt_log) and (cnt > 0)):
                    open_style = "a"
                    # split into multiple files if log becomes too long
                    if cnt_file >= n_max_lines_file:
                        cnt_file = 0
                        first = True

                    if first:
                        open_style = "w"
                        first = False
                    try:
                        with open(self.folder + "/" + self.filename, open_style) as myfile:
                            for e in buf:
                                myfile.write(e + '\r\n')
                            buf = []
                            cnt = 0
                    except:
                        Utils.print_exception(self.__class__.__name__)


