from setuptools import setup, find_packages

setup(
    name='rosbag_pickle_graph',
    version='0.1',
    packages=find_packages(exclude=['tests*']),
    license='MIT',
    description='A package to plot pickled data generated by the cbteeple fork of "rosbag-recorder"',
    long_description=open('README.md').read(),
    install_requires=['numpy','scipy', 'matplotlib'],
    url='https://github.com/cbteeple/rosbag-pickle-graph',
    author='Clark Teeple',
    author_email='cbteeple@gmail.com',
)