#! /usr/bin/env python
from __future__ import print_function
import sys
import os
import pickle
import re
import numpy as np
import scipy.interpolate as interp
import matplotlib.pyplot as plt
from itertools import cycle

from .graph_all import Grapher
from .handle_data import DataHandler


class StatGenerator:
    def __init__(self):
        self.x_field  = 'timestamp'
        self.y_fields = [{'topic':'joint_states', 'field':'position'},
                         {'topic': 'wrench', 'field':'wrench.force'},
                         {'topic': 'wrench', 'field':'wrench.torque'},
                         {'topic':'pressure_control_pressure_data', 'field':'measured'},
                         {'topic':'pressure_control_pressure_data', 'field':'setpoints'}]

        self.graph = Grapher()
        self.dh    = DataHandler()
        self.plot_raw_data = False
        self.plot_means    = False
        self.source_base_dir = None
        self.dest_dir = None
        self.file_list = None
        self.data_set = None



    # SETUP FUNCTIONS
    #------------------------------

    # Set the source directory for data
    def set_source(self, base):
        self.source_base_dir = os.path.abspath(base)


    # Set the destination directory for plots
    def set_destination(self, folder):
        self.dest_dir = os.path.abspath(folder)
        if not os.path.exists(self.dest_dir):
            os.makedirs(self.dest_dir)


    def set_flags(self, plot_raw_data=None, plot_means=None):
        if type(plot_raw_data) == bool:
            self.plot_raw_data = plot_raw_data
        if type(plot_means) == bool:
            self.plot_means    = plot_means

    # Set the x-field to use when getting data and graphing. This must be constant for all y-fields
    def set_xfield(self,xfield):
        self.xfield = xfield
        self.dh.set_xfield(xfield)
        self.graph.set_xfield(xfield)


    # Set the y-fields to use when getting data and graphing
    def set_yfields(self, yfields):
        self.yfields = yfields
        self.dh.set_yfields(yfields)
        self.graph.set_yfields(yfields)


    def get_graph_handler(self):
        return self.graph


    def get_data_handler(self):
        return self.dh


    # HELPERS
    #------------------------------

    # Get files from folders recursively
    def _get_files_recursively(self, start_directory, filter_extension=None):
        for root, dirs, files in os.walk(start_directory):
            for file in files:
                if filter_extension is None or file.lower().endswith(filter_extension):
                    #print(os.path.relpath(root, start_directory))
                    #print(file)
                    yield (root, os.path.join(root, file))


    # Check a string for substrings from a list of substrings
    def _find_from_substring_list(self,string, substring_list):
        for idx,substring in enumerate(substring_list):
            if substring in string:
                return (idx, substring)
        return (-1, None)


    # Get the number of levels in a list
    def _get_deepest_list_level(self, list_in):
        if type(list_in) is list:
            return 1 + self._get_deepest_list_level(list_in[0])
        else:
            return 0


    # Get stats from a summary file
    def _get_summary(self,filename):
        with open(filename,'r') as f:
            stats = pickle.load(f)
        print('Loaded stats from summary file')

        return stats


    # Save stats to a summary file
    def _save_summary(self, stats, metadata):
        stat_file = metadata['summary_file']
        if not metadata['summary_exists'] :
            print('Saving: %s'%(stat_file))
            with open(stat_file,'w') as f:
                pickle.dump(stats,f)
        else:
            print('Already Saved: %s'%(stat_file))


    # GET DATA
    #------------------------------

    # Get all of the filenames in a folder with a specific extension
    def get_filenames(self, data_set, extension='.pkl'):
        files = self._get_files_recursively(os.path.join(self.source_base_dir,data_set),extension)
        num_files = 0
        roots=[]
        for root, full_file in files:
            name = os.path.basename(full_file)
            folder = os.path.basename(os.path.dirname(full_file))

            num_files+=1
            
            roots.append(root)

        unique_roots=list(set(roots))

        print("Number of files: %d, Number of folders: %d"%(num_files, len(unique_roots)))
        self.data_set = data_set
        self.file_list = self._get_files_recursively(os.path.join(self.source_base_dir,data_set), extension)


    # Sort filenames into bins using a set of sort lists
    def sort_filenames(self,sort_terms, trial_regex='pos_(\d+)_' ):
        if self.file_list is None:
            print("No files to sort")
            return

        num_sort_types = self._get_deepest_list_level(sort_terms)
        files_binned = {}
        match_pos = re.compile(trial_regex)

        idx = 0
        for root, full_file in self.file_list:        
            # Check if the name contains one of the keywords for each variable
            name = os.path.basename(os.path.dirname(full_file))
            pos_name = os.path.basename(full_file)
            pos_num = int(match_pos.search(pos_name).group(1))
            
            out_file = os.path.join(self.dest_dir,os.path.relpath(full_file,start=self.source_base_dir))
            
            sorted_terms = []
            sorted_comb  = ""
            for st_idx in range(num_sort_types):
                curr_st, curr_st_name  = self._find_from_substring_list(name,sort_terms[st_idx])

                if curr_st != -1:
                    sorted_terms.append({'idx': curr_st, 'name':curr_st_name})

                    if st_idx != 0:
                        sorted_comb += ';'
                    sorted_comb += curr_st_name
            
            # if the data is not part of the set we care about, don't include it.
            if len(sorted_terms)!=num_sort_types:
                continue

            # Split out the filenames into bins
            # If bins haven't been created yet, make them
            if files_binned.get(sorted_comb,None) is None:
                files_binned[sorted_comb] = {}
            
            if files_binned[sorted_comb].get(pos_num,None) is None:
                files_binned[sorted_comb][pos_num] = {}

            if files_binned[sorted_comb][pos_num].get('data_files',None) is None:
                files_binned[sorted_comb][pos_num]['data_files'] = []
                
            # Check if a summary file already exists
            summary_file=os.path.join(root,'summary.stat')
            out_file_group= os.path.join(self.dest_dir,
                                         self.data_set,
                                         sorted_comb.replace(';','__'),
                                         "pos%04d"%(pos_num))
            files_binned[sorted_comb]['meta'] = {'summary_file': summary_file}
            files_binned[sorted_comb][pos_num]['out_file'] = out_file_group
            files_binned[sorted_comb][pos_num]['data_files'].append(full_file)

                
                
            if os.path.exists(summary_file):
                print('Summary file already exists in this folder')
                files_binned[sorted_comb]['meta']['summary_exists'] = True
                continue
            
            files_binned[sorted_comb]['meta']['summary_exists'] = False
            print(full_file)

        self.files_binned = files_binned  
    

    # Get data    
    def get_data(self, force_new_summary=False):
        allstats={}
        for key_obj in self.files_binned:
            print('Set: %s'%(key_obj))
            meta=self.files_binned[key_obj].get('meta')
            if meta['summary_exists'] and not force_new_summary:
                stats = self._get_summary(meta['summary_file'])
            else:
                stats = {}
                stats['meta']=self.files_binned[key_obj]['meta']
                for key_pos in self.files_binned[key_obj]:
                    if key_pos is 'meta':
                        continue
                    print('\tPosition: %s'%(key_pos))
                    print('\t\tAveraging data from %d files'%(len(self.files_binned[key_obj][key_pos]['data_files'])))
                    data_curr  = self.get_raw_data(file_list = self.files_binned[key_obj][key_pos]['data_files'],
                                                   out_file  = self.files_binned[key_obj][key_pos]['out_file'])
                    print('\t\tCalculating Stats')
                    stats_curr = self.calculate_stats(data_curr)
                    stats[key_pos] = stats_curr
                    stats[key_pos]['out_file'] = self.files_binned[key_obj][key_pos]['out_file']

                self._save_summary(stats, meta)
            allstats[key_obj] = stats

        self.allstats=allstats
        return allstats
    

    # Get raw data from a list of files
    def get_raw_data(self, file_list, out_file, save=True):
        idx = 0
        data_out = {}
        for full_file in file_list: 
            # Get the data and process it
            self.dh.set_filenames(full_file, out_file)            
            curr_data = self.dh.get_data(full_file)
            for key in curr_data:
                if data_out.get(key,None) is None:
                    data_out[key] = []
                    
                data_out[key].append(curr_data[key])

            # Plot raw data in individual plots
            if self.plot_raw_data:
                self.graph.set_fig_props(figsize=(6.5,4))

                if save:
                    self.graph.plot_data(curr_data, save_loc = self.dh.save_files[0])
                else:
                    self.graph.plot_data(curr_data)

        return data_out


    # Calculate statistics for an organized set of data
    def calculate_stats(self, data, metadata=None, plot_intermediate=False):
        stats_curr = {}
        # For all y_fields find the latest start time and the earliest end time
        min_time = 0
        max_time = np.inf
        base_time = None
        for key_y in data:
            data_curr = data[key_y]
            stats_curr['num_reps'] = len(data_curr)
            for run in data_curr:
                stamp = run['timestamp']
                min_stamp = np.min(stamp)
                max_stamp = np.max(stamp)

                if min_stamp>min_time:
                    min_time = min_stamp

                if max_stamp<max_time:
                    max_time = max_stamp

                if base_time is None:
                    base_time = np.array(stamp)

        # Chop the base time to match the conservative ends
        base_time = base_time[base_time>min_time]
        base_time = base_time[base_time<max_time]


        stats_curr['timestamp'] = base_time
        stats_curr['data'] = {}
        if metadata is not None:
            stats_curr['meta'] = metadata
        # For each y_field...
        for key_y in data:
            data_curr = data[key_y]

            if plot_intermediate:
                plt.figure()
                plt.ylabel(key_y)

            data_interp = {}
            data_interp['data']=[]
            data_interp['timestamp'] = base_time
            # for all columns in the y_field, do a nice interpolation                
            for idx,run in enumerate(data_curr):
                # Interpolate over the y-values of all other entries in the dataset (interp1d)
                run_time=np.array(run['timestamp'])
                run_data=np.array(run['data'])

                if plot_intermediate:
                    plt.plot(run_data, linewidth=0.25)

                interp_fun = interp.interp1d(run_time,run_data, axis=0)
                data_interp['data'].append(interp_fun(base_time))

            curr_ydata = np.array(data_interp['data'])
            means = np.mean(curr_ydata,axis=0)
            stdev = np.std(curr_ydata,axis=0)
            stats_curr['data'][key_y]={'mean': means, 'stdev': stdev}

        return stats_curr


    # pass the figure setup properties to the grapher
    def set_graph_props(self, **kwargs):
        self.graph.set_fig_props(**kwargs)


    # Plot the data
    def plot_stats(self, allstats = None, save=True):
        if allstats is None:
            allstats = self.allstats

        for key_obj in allstats:
            for key_pos in allstats[key_obj]:
                if key_pos == 'meta':
                    continue
                data = allstats[key_obj][key_pos]
                out_file = allstats[key_obj][key_pos]['out_file']

                if self.plot_means:
                    if save:
                        self.graph.plot_stats(data, save_loc = out_file )
                    else:
                        self.graph.plot_stats(data)


    # Get all the raw data
    def plot_all_raw_data(self, save=True):
        for key_obj in self.files_binned:
            data = {}
            print('Set: %s'%(key_obj))
            for key_pos in self.files_binned[key_obj]:
                if key_pos is 'meta':
                    continue
                print('\tPosition: %s'%(key_pos))
                print('\t\tReading data from %d files'%(len(self.files_binned[key_obj][key_pos]['data_files'])))
                data_curr  = self.get_raw_data(file_list = self.files_binned[key_obj][key_pos]['data_files'],
                                               out_file  = self.files_binned[key_obj][key_pos]['out_file'],
                                               save = save)
                data[key_pos] = data_curr
