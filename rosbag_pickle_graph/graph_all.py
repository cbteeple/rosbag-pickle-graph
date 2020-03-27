#! /usr/bin/env python
from __future__ import print_function
import sys
import os
import pickle
import matplotlib.pyplot as plt
from itertools import cycle

from .handle_data import DataHandler



# Graph all of your data
class Grapher:
    def __init__(self):
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
        self.dh = DataHandler()

    
    # SETUP FUNCTIONS
    #------------------------------

    # Set the x-field to use when getting data and graphing. This must be constant for all y-fields
    def set_xfield(self,xfield):
        self.x_field = xfield


    # Set the y-fields to use when getting data and graphing
    def set_yfields(self, yfields):
        self.y_fields = yfields


    # Set figure sizing properties
    def set_fig_props(self, figsize=None, dpi=None, tight_layout=None):
        if figsize is not None:
            self.fig_size = figsize

        if dpi is not None:
            self.fig_dpi  = dpi

        if tight_layout is not None:
            self.tight_layout  = tight_layout



    # MAKE FIGURES
    #------------------------------

    # Start a new figure window
    def new_plot(self):
        self.fig = plt.figure(self.plt_idx, figsize=self.fig_size, dpi=self.fig_dpi)
        self.plt_idx+=1


    # Plot the current data
    def plot_data(self, curr_data, save_loc=None):
        self.new_plot()
        success = curr_data.get('success',None)
        # Plot each y-field in a new subplot
        N = len(self.y_fields)
        for idx, y_field in enumerate(self.y_fields):
            key = self.dh.yfield_to_key(y_field)
            plt.subplot(N, 1, idx+1)
            plt.plot(curr_data[key]['timestamp'], curr_data[key]['data'], linewidth=0.575)
            plt.xlabel(self.x_field)
            plt.ylabel(y_field['field'])

            # If success is marked inside each dataset, display that in the plot title
            if idx==0:
                if success is not None:
                    if success:
                        plt.title('Trial Marked: SUCCESS')
                    else:
                        plt.title('Trial Marked: FAILED')

        # Set the plots to a "tight" layout if desired
        if self.tight_layout:
            plt.tight_layout()

        if save_loc is not None:
            self.save_plot(save_loc)

        plt.show()


    # Plot statistics
    def plot_stats(self,in_stats, palette=None, save_loc=None ):
        # Unpack the data
        data = in_stats.get('data',None)
        time = in_stats.get('timestamp',None)
        num_reps = in_stats.get('num_reps',None)
        success = in_stats.get('success',None)
        if (data is None) or (time is None):
            return False

        self.new_plot()

        # Get the color palette to use
        if palette is None:
            prop_cycle = plt.rcParams['axes.prop_cycle']
            palette = prop_cycle.by_key()['color']

        # Plot each y-field in a new subplot
        N = len(data.keys())
        idx = 0
        for y_field in self.y_fields:
            colors = cycle(palette)
            key = self.dh.yfield_to_key(y_field)
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
                if success is not None:
                    if success:
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

        if save_loc is not None:
            self.save_plot(save_loc)

        plt.show()



    # Finish the the plot and save it
    def save_plot(self, out_file=None):
        if out_file is not None:
            folder = os.path.dirname(out_file)
            file   = os.path.basename(out_file)

            if not os.path.exists(folder):
                os.makedirs(folder)

            file_blank = file.replace('.pkl','')

            plt.savefig(os.path.join(folder,file_blank+'.png'))
            plt.savefig(os.path.join(folder,file_blank+'.svg'))
