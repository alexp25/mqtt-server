from constants import Constants
import matplotlib.pylab as plt
from io import BytesIO, StringIO
from utils import Singleton
import matplotlib.pyplot as plt, mpld3
from matplotlib.pyplot import figure


class Timeseries:
    x = []
    y = []

@Singleton
class Graph:
    def __init__(self):
        self.fig_id = 0


    def plot_timeseries_multi(self, timeseries_array, title, xlabel, ylabel):
        fig = plt.figure()

        for ts in timeseries_array:
            plt.plot(ts.x, ts.y)
        self.set_disp(title, xlabel, ylabel)

        return mpld3.fig_to_html(fig)

    def plot_timeseries(self, timeseries, title, xlabel, ylabel):
        fig = plt.figure()
        plt.plot(timeseries.x, timeseries.y)
        self.set_disp(title, xlabel, ylabel)

        # sio = BytesIO()
        # fig.savefig(sio, format='png')
        # sio.seek(0)
        # return sio

        # plt.show()
        # plt.close()

        return mpld3.fig_to_html(fig)

    def set_disp(self, title, xlabel, ylabel):
        if title:
            plt.gca().set_title(title)
        if xlabel:
            plt.xlabel(xlabel)
        if ylabel:
            plt.ylabel(ylabel)
