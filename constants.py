import yaml

class Constants:
    LOOP_DELAY = 0.01

    conf = None
    @staticmethod
    def load():
        with open("config/config.yaml", 'r') as stream:
            try:
                conf = yaml.load(stream)
                print(conf)
                Constants.conf = conf
                Constants.conf["ENV"] = Constants.conf["ENV"][Constants.conf["ENV_NAME"]]
            except yaml.YAMLError as exc:
                print(exc)