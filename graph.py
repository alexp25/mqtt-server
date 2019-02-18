from constants import Constants
import matplotlib.pylab as plt
from io import BytesIO
from utils import Singleton
import matplotlib.pyplot as plt, mpld3

class Timeseries:
    x = []
    y = []

@Singleton
class Graph:
    def __init__(self):
        pass

    def plot_timeseries_multi(self, timeseries_array, title, xlabel, ylabel):
        fig = plt.figure()
        for ts in timeseries_array:
            plt.plot(ts.x, ts.y)
        self.set_disp(title, xlabel, ylabel)
        # plt.show()
        # figdata = BytesIO()
        # fig.savefig(figdata, format='png')
        # return figdata.getvalue()
        mpld3.show()

    def plot_timeseries(self, timeseries, title, xlabel, ylabel):
        fig = plt.figure()
        plt.plot(timeseries.x, timeseries.y)
        self.set_disp(title, xlabel, ylabel)
        # plt.show()
        # figdata = BytesIO()
        # fig.savefig(figdata, format='png')
        # return figdata.getvalue()
        mpld3.show()
        return mpld3.fig_to_html(fig)

    def set_disp(self, title, xlabel, ylabel):
        if title:
            plt.gca().set_title(title)
        if xlabel:
            plt.xlabel(xlabel)
        if ylabel:
            plt.ylabel(ylabel)
