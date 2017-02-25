import numpy as np
import matplotlib.pyplot as plt
import yaml
from yaml import CLoader as Loader, CDumper as Dumper
import ujson
import itertools
import argparse

# dump = yaml.dump(dummy_data, fh, encoding='utf-8', default_flow_style=False, Dumper=Dumper)
# data = yaml.load(fh, Loader=Loader)

parser = argparse.ArgumentParser()
parser.add_argument('--path', help='Path to serialized json CDDT data structure')

class Map(object):
    """ Map saved in a serialized CDDT """
    def __init__(self, data):
        print "...loading map"
        self.path = data["path"]
        self.width = data["width"]
        self.height = data["height"]
        self.data = np.array(data["data"]).transpose()

    def visualize(self):
        plt.imshow(-1*self.data, cmap="gray")
        plt.show()

class CDDTSlice(object):
    """ Contains a single slice of CDDT corresponding to a single theta value"""
    def __init__(self, data):
        # print "...loading slice"
        self.theta = data["theta"]
        self.zeros = data["zeros"]

    def num_zeros(self):
        return [len(lut_bin) for lut_bin in self.zeros]

    def ddt_dims(self):
        non_empty_zeros = filter(lambda x: len(x) > 0, self.zeros)
        min_zero = min(map(min, non_empty_zeros))
        max_zero = max(map(max, non_empty_zeros))
        return [int(np.ceil(max_zero - min_zero))+1,len(self.zeros)]

    def make_ddt(self, saw_tooth=True):
        non_empty_zeros = filter(lambda x: len(x) > 0, self.zeros)
        if len(non_empty_zeros) == 0:
            print "Empty slice, nothing to visualize"
            return

        # print map(min, self.zeros)
        min_zero = min(map(min, non_empty_zeros))
        max_zero = max(map(max, non_empty_zeros))
        height = int(np.ceil(max_zero - min_zero))+1
        ddt = np.zeros((height,len(self.zeros)))

        for x in xrange(len(self.zeros)):
            for zp in self.zeros[x]:
                y = int(zp - min_zero)
                ddt[y,x] = 1

        if saw_tooth:
            for x in xrange(len(self.zeros)):
                last = -1
                for y in xrange(height):
                    if ddt[y,x] == 1:
                        last = 0
                        ddt[y,x] = last
                    elif last >= 0:
                        last = last + 1
                        ddt[y,x] = last

        return ddt

    def visualize():
        return plt.imshow(np.sqrt(self.make_ddt()),cmap="gray")
        # plt.show()
        # print ddt #min_zero, max_zero, height


class CDDT(object):
    """ Loads a serialized CDDT datastructure for visualization and manipulation """
    def __init__(self, path):
        print "Loading CDDT:", path
        self.path = path
        print "..opening file"
        cddt_file = open(path, 'r')
        print "..loading json"
        cddt_raw = ujson.load(cddt_file)

        if not "cddt" in cddt_raw:
            print "Incorrectly formatted data, exiting."
            return

        cddt_raw = cddt_raw["cddt"]
        print "..parsing"
        self.lut_translations = np.array(cddt_raw["lut_translations"])
        self.max_range = cddt_raw["max_range"]
        self.theta_discretization = cddt_raw["theta_discretization"]
        self.map = Map(cddt_raw["map"])
        print "..loading slices"
        self.slices = map(CDDTSlice, cddt_raw["compressed_lut"])
        self.slices = self.slices[:int(len(self.slices)/2)]

    # makes a histogram of number of elements in each LUT bin
    def zeros_hist(self):
        # print self.slices[0].zeros()
        num_zeros = map(lambda x: x.num_zeros(), self.slices)
        plt.hist(num_zeros)
        plt.show()
        # print list(itertools.chain.from_iterable(num_zeros))
        # print num_zeros[0]

class SliceScroller(object):
    def __init__(self, cddt):
        # self.fig, (self.ax1,self.ax2) = plt.subplots(2, 1)
        self.fig = plt.figure()
        self.ax1 = plt.subplot(6,1,1)
        self.ax2 = plt.subplot(6,1,2)

        self.ax1 = plt.subplot2grid((4, 1), (0, 0), rowspan=3)
        self.ax2 = plt.subplot2grid((4, 1), (3, 0))
        # ax3 = plt.subplot2grid((6, 1), (2, 0))
        # ax4 = plt.subplot2grid((6, 1), (3, 0))
        # ax5 = plt.subplot2grid((6, 1), (4, 0), rowspan=2)

        # plt.subplot(6,1,3)
        # plt.subplot(2,1,2)
        # self.ax = ax
        # self.fig = fig
        self.ax1.set_title('use scroll wheel to navigate images')
        self.cddt = cddt
        self.ind = 0

        self.fig.canvas.mpl_connect('scroll_event', self.onscroll)

        self.ddts = [None]*len(self.cddt.slices)

        # dims = np.array(map(lambda x: x.ddt_dims(), self.cddt.slices))
        # max_dims = np.max(dims,axis=0)
        # print (int(max_dims[1]),int(max_dims[0]))
        # self.ddt = np.ones((max_dims[1],max_dims[0]))
        # self.ddt = 255*np.random.rand(int(max_dims[0]),int(max_dims[1]))
        # self.im = ax.imshow(self.ddt, cmap="gray")
        self.update()

        # self.get_viz()
        # print self.ddt.shape
        # self.im = ax.imshow(self.ddt, cmap="gray")        
        # self.im.axes.figure.canvas.draw()
        

    def onscroll(self, evt):
        print("Slice: %s  Theta: %s" % (self.ind, self.cddt.slices[self.ind].theta))
        self.ind = int((self.ind + evt.step) % len(self.cddt.slices))
        self.update()

    def update(self):
        plt.tight_layout()
        self.ax1.cla()
        self.ax2.cla()

        self.ax1.axis('off')

        if not isinstance(self.ddts[self.ind], np.ndarray):
        # if self.ddts[self.ind] == None:
            self.ddts[self.ind] = np.sqrt(self.cddt.slices[self.ind].make_ddt(True))
       
        ys = map(len, self.cddt.slices[self.ind].zeros)
        compression_factor = 2*self.cddt.map.width * self.cddt.map.height / (sum(ys))

        self.ax1.set_title("DDT - Reconstructed from a slice of the PCDDT, compression factor: " + str(compression_factor))
        self.ax1.set_ylabel('Theta = %s' % self.cddt.slices[self.ind].theta)
        self.ax1.imshow(self.ddts[self.ind],cmap="gray",interpolation='nearest', aspect='auto')
        
       
        self.ax2.set_title("Number of entries projected into each PCDDT bin")
        self.ax2.plot(ys)
        self.fig.canvas.draw()
        # self.im.set_data(self.ddt)
        # self.im.axes.figure.canvas.draw()






# ind = 0
# def scroll_slices(saw_tooth=True):
#   fig = plt.figure()
#   ddt = cddt.slices[10].make_ddt()
#   # im = plt.imshow(np.sqrt(ddt), cmap="gray")
#   im = plt.imshow(np.ones((100,100)), cmap="gray")
    
#   def onscroll(evt):
#       global ind
#       print "Slice:", ind, "theta:", cddt.slices[ind].theta
#       ind = int((ind + evt.step) % len(cddt.slices))
#       ddt = cddt.slices[ind].make_ddt()
#       im.set_data(ind*np.ones((100,100)))
#         im.axes.figure.canvas.draw()
#       # cddt.slices[0].visualize()
#       # plt.show()

    
#   fig.canvas.mpl_connect('scroll_event', onscroll)
#   plt.show()

if __name__ == '__main__':
    args = parser.parse_args()
    cddt = CDDT(args.path)

    
    # X = np.random.rand(20, 20, 40)
    tracker = SliceScroller(cddt)
    plt.show()


    # You probably won't need this if you're embedding things in a tkinter plot...
    # plt.ion()

    # fig, ax = plt.subplots(1, 1)
    # # X = numpy.random.rand(20, 20, 40)

    # scroller = SliceScroller(ax,fig, cddt)
    # fig.canvas.mpl_connect('scroll_event', scroller.onscroll)
    # plt.show()

    # SliceScroller(cddt)

    # scroll_slices()

    # cddt.slices[0].visualize()
    # cddt.map.visualize()
    # cddt.zeros_hist()


# from __future__ import print_function
# import numpy as np
# import matplotlib.pyplot as plt

