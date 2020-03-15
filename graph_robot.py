#! /usr/bin/env python
from __future__ import print_function
import sys
import os
import time
import pickle
import rosbag
import matplotlib.pyplot as plt

save_data_folder = 'Documents/data'

torque_order=["",]


def find_el(element, json):
    keys = element.split('.')
    rv = json
    for key in keys:
        rv = rv[key]
    return rv


class Grapher:
    def __init__(self):
        self.save_data_folder = save_data_folder
        self.plt_idx=0
        self.x_field  = 'timestamp'
        self.y_fields = [{'topic':'joint_states', 'field':'position'},
                         {'topic': 'wrench', 'field':'wrench.force'},
                         {'topic': 'wrench', 'field':'wrench.torque'}]



    def get_filenames(self, in_folder):
        self.filepath = os.path.abspath(os.path.join(os.path.expanduser('~'),self.save_data_folder,in_folder))

        self.in_files = [f for f in os.listdir(self.filepath) if (os.path.isfile(os.path.join(self.filepath, f)) and f.endswith(".pkl"))]
        self.in_files.sort()




    def plot_all(self):
        

        for file in self.in_files:
            print(file)
            self.new_plot()
            self.get_data(file)
            self.plot_current()
            self.plot_finish(file)


    
    def get_data(self,in_file):
        filename = os.path.join(self.filepath,in_file)
        with open(filename,'r') as f:
            if filename.endswith('.pkl'):
                curr_data_raw = pickle.load(f)
            f.close()

        self.curr_data={}

        for i,y_field in enumerate(self.y_fields):
            curr_topic = curr_data_raw[ y_field['topic'] ]

            times = []
            data = []
            for msg in curr_topic:
                list_el = find_el( y_field['field'], msg['msg'])

                if type(list_el) != list:
                    list_el_fix = []
                    for key, value in list_el.iteritems():
                        list_el_fix.append(value)
               
                else:
                    list_el_fix = list_el

                data.append(list_el_fix)
                times.append(msg['timestamp'])

            out = dict()
            #out['data'] = map(list, zip(*data))
            out['data'] = data
            out['timestamp'] = times

            self.curr_data[i] = out


        success_topic = curr_data_raw.get('trial_success', None)
        
        if success_topic is not None:
            self.success = find_el( 'success', success_topic[0]['msg'])
        else:
            self.success = None



    def new_plot(self):
        self.fig = plt.figure(self.plt_idx)
        self.plt_idx+=1
        

    def plot_current(self):
        N = len(self.y_fields)
        for idx, y_field in enumerate(self.y_fields):
            plt.subplot(N, 1, idx+1)
            plt.plot(self.curr_data[idx]['timestamp'], self.curr_data[idx]['data'], linewidth=0.575)
            plt.xlabel(self.x_field)
            plt.ylabel(y_field['field'])

            if idx==0:
                if self.success is not None:
                    if self.success:
                        plt.title('Trial Marked: SUCCESS')
                    else:
                        plt.title('Trial Marked: FAILED')



    def plot_finish(self,in_file=None):
        
        plt.savefig(os.path.join(self.filepath,in_file.replace('.pkl','.png')))
        plt.savefig(os.path.join(self.filepath,in_file.replace('.pkl','.svg')))
        plt.show()





if __name__ == '__main__':
    if  len(sys.argv) ==2:
        graph = Grapher()
        graph.get_filenames(str(sys.argv[1]))
        graph.plot_all()