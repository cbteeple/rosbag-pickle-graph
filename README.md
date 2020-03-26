# rosbag-pickle-graph (the package)
Graph the data stored by my [rosbag-pickler](https://github.com/cbteeple/rosbag-recorder).

## Installation
1. Download the package
2. Navigate into the main folder
3. `pip install .`

## Usage
``` python
import rosbag_pickle_graph as rpg

robot_graph = rpg.Grapher()
robot_graph.set_filenames('data', 'output/out_file.pkl')
robot_graph.plot_all()

```


