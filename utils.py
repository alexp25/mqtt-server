import sys
from threading import Thread


class Singleton:
    """
    A non-thread-safe helper class to ease implementing singletons.
    This should be used as a decorator -- not a metaclass -- to the
    class that should be a singleton.

    The decorated class can define one `__init__` function that
    takes only the `self` argument. Also, the decorated class cannot be
    inherited from. Other than that, there are no restrictions that apply
    to the decorated class.

    To get the singleton instance, use the `instance` method. Trying
    to use `__call__` will result in a `TypeError` being raised.

    """

    def __init__(self, decorated):
        self._decorated = decorated

    def instance(self):
        """
        Returns the singleton instance. Upon its first call, it creates a
        new instance of the decorated class and calls its `__init__` method.
        On all subsequent calls, the already created instance is returned.

        """
        try:
            return self._instance
        except AttributeError:
            self._instance = self._decorated()
            return self._instance

    def __call__(self):
        raise TypeError('Singletons must be accessed through `instance()`.')

    def __instancecheck__(self, inst):
        return isinstance(inst, self._decorated)

class Utils:
    @staticmethod
    def format_exception(msg):
        exc_type, exc_value = sys.exc_info()[:2]
        exceptionMessage = str(exc_type.__name__) + ': ' + str(exc_value)
        em1 = 'Error on line {}'.format(sys.exc_info()[-1].tb_lineno)
        msg1 = msg + ' ' + em1 + ', ' + exceptionMessage
        return msg1

    @staticmethod
    def print_exception(msg):
        msg1 = Utils.format_exception(msg)
        print(msg1)

    @staticmethod
    def get_sensor_id_encoding(id, topic_code):
        # print("get sensor id: " + str(id) + ", topic code: " + str(topic_code))
        id = topic_code * 1000 + id
        return id

    @staticmethod
    def log(msg):
        print(msg)
