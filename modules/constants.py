import yaml

class Constants:
    LOOP_DELAY = 0.01

    conf = {}
    @staticmethod
    def load():
        with open("config/config.yaml", 'r') as stream:
            try:
                conf = yaml.load(stream)
                print(conf)
                Constants.conf = conf
            except yaml.YAMLError as exc:
                print(exc)
        
        with open("config/" + Constants.conf["ENV"][Constants.conf["ENV_NAME"]], "r") as stream:
            try:
                conf = yaml.load(stream)
                print(conf)
                Constants.conf["ENV"] = conf
            except yaml.YAMLError as exc:
                print(exc)
            