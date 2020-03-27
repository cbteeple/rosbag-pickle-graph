import rosbag_pickle_graph as rpg

source_base_dir = 'data'
dest_dir        = 'data_plot'

data_set = "test"

plot_raw_data = True
save_raw_graphs = True

plot_means    = True
save_mean_graphs = True

force_new_summary = False

grasp_types = ["top_grasp","plop_grasp","swoosh_grasp"]
object_types = ["branch2_90","branch4_90","branch6_90","branch4_45","branch4_135",
               "tube25_side","tube64_side","tube25_vert","tube64_vert","taurus_big_vert",'sphere']

grasp_types_pretty = ["Descend", "Plop", "Side-Swipe"]
object_types_pretty = ["Branched (2x90)","Branched (4x90)","Branched (6x90)","Branched (4x45)",
                       "Branched (4x135)",
               "25 mm Tube (side)","64 mm Tube (side)","25 mm Tube (vert)","64 mm Tube (vert)",
                       "Taurus (vert)",'Sphere']

xfield  = 'timestamp'
yfields = [{'topic':'joint_states', 'field':'position'},
           {'topic': 'wrench', 'field':'wrench.force'},
           {'topic': 'wrench', 'field':'wrench.torque'}]

# Initialize the statistics generator
stat = rpg.StatGenerator()
stat.set_source(source_base_dir)
stat.set_destination(dest_dir)
stat.set_flags(plot_raw_data, plot_means)
stat.set_xfield(xfield)
stat.set_yfields(yfields)

# Get the filenames and sort them
stat.get_filenames(data_set)
stat.sort_filenames([object_types,grasp_types])

# Read in the data from summaries or calculate from raw data
stat.get_data(force_new_summary)

# Graph the mean data
stat.set_graph_props(figsize=(6.5,4), tight_layout=False)
stat.plot(save = save_mean_graphs)