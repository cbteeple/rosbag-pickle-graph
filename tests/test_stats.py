import rosbag_pickle_graph

def test_graph():
    statGen = rosbag_pickle_graph.StatGenerator()
    
    graph=rosbag_pickle_graph.Grapher()
    graph.get_filenames('data/top_grasp_2_sphere_20200316_203800')
    graph.plot_all()

    for field in graph.y_fields:
        key = graph.yfield_to_key(field)
        if len(graph.curr_data[key]['data']) ==0
            assert False
            break
    assert True