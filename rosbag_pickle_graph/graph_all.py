#! /usr/bin/env python
from __future__ import print_function
import sys
import os
import pickle
import matplotlib.pyplot as plt
from itertools import cycle


save_data_folder = 'Documents/data'


# Graph all of your data
class Grapher:
    def __init__(self):
        self.save_data_folder = save_data_folder
        self.plt_idx=0
        self.x_field  = 'timestamp'
        self.y_fields = [{'topic':'joint_states', 'field':'position'},
                         {'topic': 'wrench', 'field':'wrench.force'},
                         {'topic': 'wrench', 'field':'wrench.torque'},
                         {'topic':'pressure_control_pressure_data', 'field':'measured'},
                         {'topic':'pressure_control_pressure_data', 'field':'setpoints'}]

        self.fig_size=(6.5, 3)
        self.fig_dpi=300
        self.tight_layout = False
        self.success = None
        self.full_files = []

    
    # SETUP FUNCTIONS
    #------------------------------

    # Set the x-field to use when getting data and graphing. This must be constant for all y-fields
    def set_xfield(self,xfield):
        self.x_field = xfield


    # Set the y-fields to use when getting data and graphing
    def set_yfields(self, yfields):
        self.y_fields = yfields


    # Set the y-fields to use when getting data and graphing
    def set_save_folder(self, folder):
        self.save_data_folder = folder


    # Get the filenames of all files in a given folder
    def get_filenames(self, in_folder, save_folder=None):
        self.filepath = os.path.abspath(os.path.join(os.path.expanduser('~'),self.save_data_folder,in_folder))

        self.in_files = [f for f in os.listdir(self.filepath) if (os.path.isfile(os.path.join(self.filepath, f)) and f.endswith(".pkl"))]
        self.in_files.sort()

        self.full_files = [os.path.join(self.filepath, f) for f in self.in_files]
        if save_folder is None:
            save_folder = os.path.abspath(os.path.join(os.path.expanduser('~'),self.save_data_folder,in_folder))
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


    # Set figure sizing properties
    def set_fig_props(self, figsize=None, dpi=None):
        if figsize is not None:
            self.fig_size = figsize

        if dpi is not None:
            self.fig_dpi  = dpi



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

    # Make a plot for each file in the file list 
    def plot_all(self):
        for idx, file in enumerate(self.full_files):
            print(file)
            self.new_plot()
            self.get_data(file)
            self.plot_current()
            self.plot_finish(self.save_files[idx])

        
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

        success_topic = curr_data_raw.get('trial_success', None)
        
        if success_topic is not None:
            self.success = self.find_el( 'success', success_topic[0]['msg'])
        else:
            self.success = None


    # MAKE FIGURES
    #------------------------------

    # Start a new figure window
    def new_plot(self):
        self.fig = plt.figure(self.plt_idx, figsize=self.fig_size, dpi=self.fig_dpi)
        self.plt_idx+=1


    # Plot the current data
    def plot_current(self):
        # Plot each y-field in a new subplot
        N = len(self.y_fields)
        for idx, y_field in enumerate(self.y_fields):
            plt.subplot(N, 1, idx+1)
            plt.plot(self.curr_data[idx]['timestamp'], self.curr_data[idx]['data'], linewidth=0.575)
            plt.xlabel(self.x_field)
            plt.ylabel(y_field['field'])

            # If success is marked inside each dataset, display that in the plot title
            if idx==0:
                if self.success is not None:
                    if self.success:
                        plt.title('Trial Marked: SUCCESS')
                    else:
                        plt.title('Trial Marked: FAILED')

        # Set the plots to a "tight" layout if desired
        if self.tight_layout:
            plt.tight_layout()


    # Plot statistics
    def plot_stats(self,in_stats, palette =None ):
        # Unpack the data
        data = in_stats.get('data',None)
        time = in_stats.get('timestamp',None)
        num_reps = in_stats.get('num_reps',None)
        if (data is None) or (time is None):
            return False

        # Get the color palette to use
        if palette is None:
            prop_cycle = plt.rcParams['axes.prop_cycle']
            palette = prop_cycle.by_key()['color']

        # Plot each y-field in a new subplot
        N = len(data.keys())
        idx = 0
        for y_field in self.y_fields:
            colors = cycle(palette)
            key = self.yfield_to_key(y_field)
            plt.subplot(N, 1, idx+1)
            plt.plot(time, data[key]['mean'], linewidth=0.575, color='k')
            for col_idx in range(data[key]['mean'].shape[1]):
                plt.fill_between(time,
                     data[key]['mean'][:,col_idx]-data[key]['stdev'][:,col_idx],
                     data[key]['mean'][:,col_idx]+data[key]['stdev'][:,col_idx],
                     color=next(colors))
            plt.ylabel(y_field['field'])

            # If success is marked inside each dataset, display that in the plot title
            if idx==0:
                if self.success is not None:
                    if self.success:
                        plt.title('Trial Marked: SUCCESS')
                    else:
                        plt.title('Trial Marked: FAILED')
            idx+=1

        plt.xlabel("Time (sec)")
        ax = plt.gca()
        
        # Display the number of trials if that is reported
        if num_reps is not None:
            ax_width = ax.get_xlim()[1]-ax.get_xlim()[0]
            ax_height = ax.get_ylim()[1]-ax.get_ylim()[0]
            plt.text(ax.get_xlim()[1]-ax_width*0.01,
                     ax.get_ylim()[1]-ax_height*0.05,
                     "n = %d"%(num_reps),
                     verticalalignment='top',
                     horizontalalignment='right')

        # Set the plots to a "tight" layout if desired
        if self.tight_layout:
            plt.tight_layout()


    # Finish the the plot and save it
    def plot_finish(self, in_file=None):
        if in_file is not None:
            folder = os.path.dirname(in_file)
            file   = os.path.basename(in_file)

            if not os.path.exists(folder):
                os.makedirs(folder)

            file_blank = file.replace('.pkl','')

            plt.savefig(os.path.join(folder,file_blank+'.png'))
            plt.savefig(os.path.join(folder,file_blank+'.svg'))
        
        plt.show()


# Do some default things if the file is the main file.
if __name__ == '__main__':
    if  len(sys.argv) ==2:
        graph = Grapher()
        graph.get_filenames(str(sys.argv[1]))
        graph.plot_all()