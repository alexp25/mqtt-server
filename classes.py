

class MQTTMessage:

    def __init__(self, orig=None):
        self.topic = ""
        self.id = 0
        self.type = 0
        self.ts = None

        self.data = []
        if orig is not None:
            self.copy_constructor(orig)

    def copy_constructor(self, orig):
        self.topic = orig.topic
        self.id = orig.id
        self.type = orig.type
        self.data = orig.data
        self.ts = orig.ts



class Sensor:
    def __init__(self, orig=None):
        self.id = ""
        self.type = 0
        self.topic_code = 0
        self.n_channel = 0
        self.log_rate = 0
        self.flag1 = False
        self.data_buffer = []
        self.current_data = None
        self.ts = None
        self.log_ts = None

        self.topic_name = ""

        if orig is not None:
            self.copy_constructor(orig)

    def copy_constructor(self, orig):
        self.id = orig.id
        self.type = orig.type
        self.topic_code = orig.topic_code
        self.n_channel = orig.n_channel
        self.log_rate = orig.log_rate
        self.data_buffer = orig.data_buffer
        self.current_data = orig.current_data
        self.ts = orig.ts
        self.flag1 = orig.flag1
        self.log_ts = orig.log_ts
        self.topic_name = orig.topic_name