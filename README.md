# Welcome to RatLabv3!

Ratlab presents an experimental setup for studying oriospatial cells in the hippocampus. In particular, the software allows one to explore the generation of place cells and head direction cells in unknown spatial environments. The simulations use a hierarchical Slow Feature Analysis (SFA) network, which has already been shown to produce spatially selective outputs matching the firing patterns of such neurons [[1](http://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.0030166), [2](http://journal.frontiersin.org/article/10.3389/fncom.2015.00051/full)].

This repository offers an update of the RatLab software (Fabian Schönfeld 2017) to python 3. The commands, functionality and scope of the software remain unchanged, and are described in detail in the [[original GitLab repository](https://gitlab.com/fabschon/ratlab)]. In order to cite Ratlab in your own work, please refer to [this paper](http://journal.frontiersin.org/article/10.3389/fncom.2013.00104/full).


### System requirements

RatLab is written in Python and uses the following libraries: 

* [Python](https://www.python.org/)
* [NumPy](http://www.numpy.org/)
* [Modular Toolkit for Data Processing](http://mdp-toolkit.sourceforge.net/) (MDP)
* [Pillow](https://pillow.readthedocs.io/en/stable/)  (Updated from PIL in the previous version of Ratlab)
* [PyOpenGL](http://pyopengl.sourceforge.net/)

The `requirements.txt` file shows the versions of each library that can be used for Python 3.8.5. Once you have python, the other libraries can all be installed using pip. However, if you are using a Windows machine you will need to download PyOpenGL from [[PyPi](https://pypi.org/project/PyOpenGL/#files)] and install it manually using:

	$ tar -zxvf PyOpenGL-3.1.5.tar.gz
	$ cd PyOpenGL-3.1.5
	$ python setup.py install
