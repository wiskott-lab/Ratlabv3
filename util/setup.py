#==============================================================================
#
#  Copyright (C) 2016 Fabian Schoenfeld
#
#  This file is part of the ratlab software. It is free software; you can
#  redistribute it and/or modify it under the terms of the GNU General Public
#  License as published by the Free Software Foundation; either version 3, or
#  (at your option) any later version.
#
#  This library is distributed in the hope that it will be useful, but WITHOUT
#  ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
#  FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
#  more details.
#
#  You should have received a copy of the GNU General Public License along with
#  a special exception for linking and compiling against the pe library, the
#  so-called "runtime exception"; see the file COPYING. If not, see:
#  http://www.gnu.org/licenses/
#
#==============================================================================


import sys
import math
import numpy
import pickle
import freezeable
Freezeable = freezeable.Freezeable

#====================================================================[ Control ]

# +Setup
# |
# +---+constants
# |   |
# |   +->RAD2DEG: constant to convert radian angles into degree angles [def: 180.0/math.pi]
# |   +->DEG2RAD: constant to convert degree angles into radian angles [def: math.pi/180.0]
# |
# +---+world
# |   |
# |   +->type:        denotes the world type: 'box', 'star', 'T', 'circle', 'file' [def: 'box']
# |   +->dim:         tuple containing the defining dimensions of the respective world type 
# |   |               +->box:    ( <length>, <width>, <height> ) [def: 300x200x100]
# |   |               +->star:   ( <arms>, <arm_width>, <arm_length>, <arm_height> )
# |   |               +->T:      ( <vertical_length>, <vertical_width>, <horizontal_length>, <horizontal_width>, <wall_height> )
# |   |               +->circle: ( <radius>, <segments>, <wall_height> )
# |   |               +->file    ( <file_name> )
# |   +->box_dim:     tuple containing the dimensions of a default box [def: 80x60x60]
# |   +->boxmix:      randomly choosen textures for rectangular obstacles [ef: false]
# |   +->wallmix:     uniform or mixed wall texturing [def: true]
# |   +->wall_offset: distance from the world edges that will not be accessed
# |   +->cam_height:  height of the camera within the world [def: 10.0]
# |   +->obstacles:   list of rectangular obstacles [def: <empty list>]
# |   +->limits:      min/max coordinates of the world [determined by world.py]
# |   |
# |   +->color_background:     background color [def: (0.0,0.0,0.0)]
# |   +->color_rat_marker:     color used to draw the rat marker [def: (0.6,0.0,0.0)]
# |   +->color_rat_path:       color used to draw the rat's path [def: (0.0,0.3,0.6)]
# |   +->color_sketch_default: color used when sketching with uniform colors [def: (0.0,0.0,0.8)]
# |
# +---+opengl
# |   |
# |   +->clip_near:            distance to near clipping plane [def: 2.0]
# |   +->clip_far:             distance to far clipping plane [def: 512.0]
# |
# +---+rat
#     |
#     +->color:    denotes the output color mode: 'greyscale', 'RGB', or 'duplex' [def: 'RGB']
#     +->fov:      rat field of view [def: 320.0]
#     +->arc:      arc defining rat mobility  [320.0]
#     +->path_dev: deviation from beeline when following a path [def: 0.3]
#     +->path_mom: momentum/smoothness of the rat's path [def: 0.8]
#     +->bias:	   sector denoting an optional movement bias [def: (0.0,0.0)]
#     +->bias_s:   vcalar strength factor of the movement bias [def: 0.0]
#     +->speed:    speed multiplyer for the movement of the rat [def: 1.0]


# empty utility class
class EmptyOptionContainer( Freezeable ):
    def __init__( self ):
        pass

# global control panel
class Setup( Freezeable ):

	def __init__( self, filename=None ):

		self.constants = EmptyOptionContainer()
		self.constants.RAD2DEG = 180.0/math.pi
		self.constants.DEG2RAD = math.pi/180.0
		self.constants.freeze()

		self.world = EmptyOptionContainer()
		self.world.type        = 'box'
		self.world.dim         = numpy.array([60,40,10])
		self.world.box_dim	   = numpy.array([ 8, 8, 5])
		self.world.boxmix      = False
		self.world.wallmix     = True
		self.world.wall_offset = 5.0
		self.world.cam_height  = 3
		self.world.obstacles   = []
		self.world.limits      = numpy.array([numpy.NAN,numpy.NAN,numpy.NAN,numpy.NAN])
		self.world.color_background     = numpy.array([0.0,0.0,0.0])
		self.world.color_rat_marker     = numpy.array([0.6,0.0,0.0])
		self.world.color_rat_path       = numpy.array([1.0,1.0,1.0])
		self.world.color_sketch_default = numpy.array([0.0,0.0,0.8])
		self.world.freeze()

		self.opengl = EmptyOptionContainer()
		self.opengl.clip_near = 0.5
		self.opengl.clip_far  = 1024
		self.opengl.freeze()

		self.rat = EmptyOptionContainer()
		self.rat.color	   = 'RGB'
		self.rat.fov       = numpy.array([320.0,40.0])
		self.rat.arc       = 320.0
		self.rat.path_dev  = 0.125
		self.rat.path_mom  = 0.55
		self.rat.bias	   = numpy.array([0.0,0.0])
		self.rat.bias_s	   = 0.0
		self.rat.speed     = 1.0
		self.rat.path      = None
		self.rat.path_loop = False
		self.rat.freeze()

		self.freeze()

		# optional: overwrite default values
		if filename != None:
			self.fromFile( filename )

	def toString(self):
		# world parameters
		s  = str('world.type').ljust(20)         + str(self.world.type)                    			+'\n'
		s += str('world.dim').ljust(20)          + str(self.world.dim).translate(str.maketrans(dict.fromkeys('[]')))         +'\n'
		s += str('world.box_dim').ljust(20)      + str(self.world.box_dim).translate(str.maketrans(dict.fromkeys('[]')))     +'\n'
		s += str('world.boxmix').ljust(20)       + str(self.world.boxmix)                  +'\n'
		s += str('world.wallmix').ljust(20)      + str(self.world.wallmix)                 +'\n'
		s += str('world.wall_offset').ljust(20)  + str(self.world.wall_offset)             +'\n'
		s += str('world.cam_height').ljust(20)   + str(self.world.cam_height)              +'\n'
		s += str('world.obstacles').ljust(20)    + str(self.world.obstacles)   			   +'\n'
		s += str('world.limits').ljust(20)       + str(self.world.limits).translate(str.maketrans(dict.fromkeys('[]')))      +'\n\n'
		# rat paramerters
		s += str('rat.color').ljust(20)    + str(self.rat.color)            +'\n'
		s += str('rat.fov').ljust(20)      + str(self.rat.fov).translate(str.maketrans(dict.fromkeys('[]')))  +'\n'
		s += str('rat.arc').ljust(20)      + str(self.rat.arc)              +'\n'
		s += str('rat.path_dev').ljust(20) + str(self.rat.path_dev)         +'\n'
		s += str('rat.path_mom').ljust(20) + str(self.rat.path_mom)         +'\n'
		s += str('rat.bias').ljust(20)     + str(self.rat.bias).translate(str.maketrans(dict.fromkeys('[]'))) +'\n'
		s += str('rat.bias_s').ljust(20)   + str(self.rat.bias_s)           +'\n'
		s += str('rat.speed').ljust(20)    + str(self.rat.speed)            +'\n'
		s += '' if (self.rat.path==None) else (str('rat.path').ljust(20)+self.rat.path+'\n')
		# string
		return s

	def toFile( self, filename ):
		f = open(filename, 'w')
		f.write( self.toString() )
		f.close()
		
	def fromFile( self, filename ):
		# file
		f = open( filename, 'r' )
		# world type and dim
		self.world.type = f.readline().strip('world.type').strip()
		s = f.readline().strip('world.dim').split()
		if self.world.type == 'file': self.world.dim = s[0]
		if self.world.type == 'box' or self.world.type == 'circle': self.world.dim = numpy.array( [ float(s[0]), float(s[1]), float(s[2]) ] )
		if self.world.type == 'star': self.world.dim = numpy.array( [ float(s[0]), float(s[1]), float(s[2]), float(s[3]) ] )
		if self.world.type == 'T': self.world.dim = numpy.array( [ float(s[0]), float(s[1]), float(s[2]), float(s[3]), float(s[4]) ] )
		# miscellaneous
		s = f.readline().strip('world.box_dim').split()
		self.world.box_dim = numpy.array( [ float(s[0]), float(s[1]), float(s[2]) ] )
		self.world.boxmix = True if f.readline().strip('world.boxmix').strip() == 'True' else False
		self.world.wallmix = True if f.readline().strip('world.wallmix').strip() == 'True' else False
		self.world.wall_offset = float(f.readline().strip('world.wall_offset'))
		self.world.cam_height = float(f.readline().strip('world.cam_height'))
		# obstacles
		s = f.readline().strip('world.obstacles').split()
		if self.world.type != 'file':
			s = [ float(i.strip('[,]\n')) for i in s if i.strip('[,]\n')!='' ]  # clear & convert
			self.world.obstacles = [ s[i:i+4] for i in range(0,len(s),4) ]      # group in fours
		# world limits
		s = f.readline().strip('world.limits').split()
		self.world.limits = numpy.array( [ float(s[0]), float(s[1]), float(s[2]), float(s[3]) ] )
		# rat parameters
		f.readline()
		self.rat.color = f.readline().strip('rat.color').strip()
		s = f.readline().strip('rat.fov').split()
		self.rat.fov = numpy.array([ float(s[0]), float(s[1]) ])
		self.rat.arc = float(f.readline().strip('rat.arc'))
		self.rat.path_dev = float(f.readline().strip('rat.path_dev'))
		self.rat.path_mom = float(f.readline().strip('rat.path_mom'))
		s = f.readline().strip('rat.bias').split()
		self.rat.bias = numpy.array([ float(s[0]), float(s[1]) ])
		self.rat.bias_s = float(f.readline().strip('rat.bias_s'))
		self.rat.speed = float(f.readline().strip('rat.speed'))
		path_file = f.readline().strip('rat.path').split()
		self.rat.path = None if path_file == [] else path_file[0]
		# file
		f.close()
