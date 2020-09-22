print('system imports..')
import os
import sys
import time
import struct
import string
import pickle

print('math imports..')
import mdp
import math
import numpy
import random

print('image imports..')
from PIL import Image
from PIL import ImageDraw

print('OpenGL imports..')
from OpenGL.GLUT import *
from OpenGL.GLU  import *
from OpenGL.GL   import *

print('Everything seems to be in order.')
print('Versions you are using:')
print('MDP:    ', mdp.__version__)
print('Numpy:  ', numpy.__version__)
print('PIL:    ', Image.__version__)
print('OpenGL: ', OpenGL.__version__)
