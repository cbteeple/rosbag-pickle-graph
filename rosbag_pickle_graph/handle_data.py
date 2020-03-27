#! /usr/bin/env python
from __future__ import print_function
import sys
import os
import pickle
import matplotlib.pyplot as plt
from itertools import cycle



# Get all of your data
class DataHandler:
    def __init__(self):
        self.data_source_folder = ''
        self.x_field  = 'timestamp'
        self.y_fields = [{'topic':'joint_states', 'field':'position'},
                         {'topic': 'wrench', 'field':'wrench.force'},
                         {'topic': 'wrench', 'field':'wrench.torque'},
                         {'topic':'pressure_control_pressure_data', 'field':'measured'},
                         {'topic':'pressure_control_pressure_data', 'field':'setpoints'}]

        self.fig_size=(6.5, 3)
        self.fig_dpi=300
        self.tight_layout = False
        self.full_files = []


    
    # SETUP FUNCTIONS
    #------------------------------

    # Set the x-field to use when getting data and graphing. This must be constant for all y-fields
    def set_xfield(self,xfield):
        self.x_field = xfield


    # Set the y-fields to use when getting data and graphing
    def set_yfields(self, yfields):
        self.y_fields = yfields


    # Set the source folder to use when getting data and graphing
    def set_source_folder(self, folder):
        self.data_source_folder = folder


    # Get the filenames of all files in a given folder
    def get_filenames(self, in_folder, save_folder=None):
        self.filepath = os.path.abspath(os.path.join(os.path.expanduser('~'),self.data_source_folder,in_folder))

        self.in_files = [f for f in os.listdir(self.filepath) if (os.path.isfile(os.path.join(self.filepath, f)) and f.endswith(".pkl"))]
        self.in_files.sort()

        self.full_files = [os.path.join(self.filepath, f) for f in self.in_files]
        if save_folder is None:
            save_folder = os.path.abspath(os.path.join(os.path.expanduser('~'),self.data_source_folder,in_folder))
            self.save_files  = [os.path.join(save_folder, f) for f in self.in_files]


    # Set the list of filenames to use
    def set_filenames(self, in_files, save_folder=None):
        if isinstance(in_files, list):
            self.full_files = in_files
        
            if save_folder is None:
                self.save_files = self.full_files
            elif isinstance(save_folder, list):
                self.save_files = [os.path.join(save_folder[idx], os.path.basename(f)) for idx, f in enumerate(self.full_files)]
            else:
                self.save_files = [os.path.join(save_folder, os.path.basename(f)) for f in self.full_files]

        else:
            self.full_files = [in_files]

            if save_folder is None:
                self.save_files = self.full_files
            else:
                self.save_files = [os.path.join(save_folder, os.path.basename(f)) for f in self.full_files]



    # HELPER FUNCTIONS
    #------------------------------

    # Convert a y-field to a suitable dictionary key
    def yfield_to_key(self,yfield):
        return yfield['topic'] +';'+yfield['field']


    # Convert a suitable dictionary key to a y-field
    def key_to_yfield(self,key):
        sep = key.split(';')
        return {'topic':sep[0], 'field':sep[1]}


    # Find the elements from the pickeled file structure
    def find_el(self,element, json):
        keys = element.split('.')
        rv = json
        for key in keys:
            rv = rv[key]
        return rv



    # DO WORK
    #------------------------------

        
    # Get the data from a particular file based on the desired y-fields
    def get_data(self,in_file):
        filename = in_file
        with open(filename,'r') as f:
            if filename.endswith('.pkl'):
                curr_data_raw = pickle.load(f)
            f.close()

        self.curr_data=dict()

        for i,y_field in enumerate(self.y_fields):
            curr_topic = curr_data_raw[ y_field['topic'] ]

            times = []
            data = []
            for msg in curr_topic:
                list_el = self.find_el( y_field['field'], msg['msg'])

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

            out_key = self.yfield_to_key(y_field)
            self.curr_data[out_key] = out

        return self.curr_data