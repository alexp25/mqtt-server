from typing import List

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
        self.id = 0
        self.raw_id = 0
        self.type = 0
        self.topic_code = 0
        self.topic_name: str = ""
        self.log_rate = 0
        self.data_buffer: List[MQTTMessage] = []
        self.current_data: MQTTMessage = None
        self.ts = None
        self.log_ts = None       

        if orig is not None:
            self.copy_constructor(orig)

    def copy_constructor(self, orig):
        self.id = orig.id
        self.raw_id = orig.raw_id
        self.type = orig.type
        self.topic_code = orig.topic_code

        self.log_rate = orig.log_rate
        self.data_buffer = orig.data_buffer
        self.current_data = orig.current_data
        self.ts = orig.ts
        self.log_ts = orig.log_ts
        self.topic_name = orig.topic_name