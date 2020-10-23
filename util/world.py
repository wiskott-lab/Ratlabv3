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


#======================================================================[ Setup ]

# system
import os
import sys
import types
import string

# python image library
from PIL import Image as img

# math
import math
import numpy
import random as rnd

# OpenGL
from OpenGL.GLUT import *
from OpenGL.GLU  import *
from OpenGL.GL   import *

# utilities / own
from util.setup import *
from opengl_text import *

#defines
def_MARKER_HEIGHT =   0.1  # default height of drawn debug markers
def_CUSTOM_HEIGHT =  12.0  # default height for walls in custom mazes ### adapted for epuck scenario atm


#===============================================================[ Wall Segment ]

class Wall( Freezeable ):

	def __init__( self, left_end, right_end, height, texture=None, offset=None ):
		self.vec_from = left_end
		self.vec_to   = right_end
		self.height   = height
		self.normal   = numpy.array( [(self.vec_to-self.vec_from)[1],-(self.vec_to-self.vec_from)[0]] )
		self.normal  /= numpy.sqrt( self.normal[0]**2 + self.normal[1]**2 )
		self.texture  = 0 if texture==None else texture
		self.offset   = 0.0 if offset==None else offset

	# check wether a given point lies in front of the wall
	def facingFront( self, pos ):
		if numpy.dot( pos-(self.vec_from+0.5*wall_vec), self.normal ) < 0.0: 
			return False
		else:
			return True

	# check wether a given point lies closer to the wall than the allowed offset
	def proximityAlert( self, pos ):
		wall_vec = self.vec_to - self.vec_from
		mu  = (pos[0]-self.vec_from[0])*(self.vec_to[0]-self.vec_from[0]) + (pos[1]-self.vec_from[1])*(self.vec_to[1]-self.vec_from[1])
		mu /= wall_vec[0]**2 + wall_vec[1]**2
		if mu < 0.0:
			return numpy.sqrt( (pos-self.vec_from)[0]**2 + (pos-self.vec_from)[1]**2 ) < self.offset
		elif mu > 1.0:
			return numpy.sqrt( (pos-self.vec_to)[0]**2 + (pos-self.vec_to)[1]**2 ) < self.offset
		else:
			proj = self.vec_from + mu*wall_vec
			dist = numpy.sqrt( (proj-pos)[0]**2 + (proj-pos)[1]**2 )
			return dist < self.offset

	# check wether the path between two positions crosses the wall segment
	def crossedBy( self, pos_old, pos_new ):
		# check 1: old position in front, new position behind wall segment
		wall_vec = self.vec_to - self.vec_from
		if not ( numpy.dot( pos_old-(self.vec_from+0.5*wall_vec), self.normal ) > 0.0 and \
				 numpy.dot( pos_new-(self.vec_from+0.5*wall_vec), self.normal ) < 0.0 ):
			return False
		# determine crossing point (moving parallel to wall is cought by check 1)
		xy = self.vec_to-self.vec_from
		uv = pos_new-pos_old
		l = ( pos_old[1] + (self.vec_from[0]*uv[1]-pos_old[0]*uv[1])/uv[0] - self.vec_from[1] ) / ( (1.0-(xy[0]*uv[1])/(uv[0]*xy[1])) * xy[1] )
		m = ( self.vec_from[0] + l*xy[0] - pos_old[0] ) / uv[0]
		# check C: intersection lies between old & new position, and also within wall segment limits
		if l >= 0 and l <= 1.0 and \
           m >= 0 and m <= 1.0:
			return True
		else:
			return False


#============================================================[ Texture Catalog ]

class Textures:

	def __init__( self ):
		# texture dictionary index
		self.index = {}
		# texture id's by category
		self.floor   = []
		self.wall    = []
		self.crate   = []
		self.skybox  = None
		# find available textures
		tex_list = os.listdir( './textures' )
		tex_list.sort()
		for f in tex_list:
			s = str.split( f, '.' )[0]
			if 'floor' not in s and 'wall' not in s and 'crate' not in s and 'skybox' not in s: continue
			i = self.load( 'textures/'+f )
			# add to category
			if   'floor'   in s: self.floor.append( i )
			elif 'wall'    in s: self.wall.append ( i )
			elif 'crate'   in s: self.crate.append( i )
			elif 'skybox'  in s: self.skybox  = i
			# add to index
			self.index[s] = i
		# assign random colors to textures
		self.sketch_color = numpy.zeros([len(self.floor)+len(self.wall)+len(self.crate)+2, 3]) # +2 b/c skybox & and tex 0
		for i in range(self.sketch_color.shape[0]):
			self.sketch_color[i] = numpy.array([min(numpy.random.random()+0.2,1.0),min(numpy.random.random()+0.2,1.0),min(numpy.random.random()+0.2,1.0)])
		self.sketch_color[0] = numpy.array([0.0,0.0,0.8]) # one default color

	def load( self, filename, ):
		mipmapping = False
		# open image
		src_img = img.open( filename )
		img_str = src_img.tobytes( 'raw', 'RGB', 0, -1 )
		# opengl image id
		img_id = glGenTextures(1)
		glBindTexture( GL_TEXTURE_2D, img_id )
		# texture parameters
		glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP)
		glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP)
		glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
		if mipmapping:
			glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_NEAREST )
		else:
			glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST);
		glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE)
		# store texture image (use mipmapping to kill off render artifacts)
		glPixelStorei( GL_UNPACK_ALIGNMENT, 1 )
		if mipmapping:
			gluBuild2DMipmaps( GL_TEXTURE_2D, 
							   3, 
							   src_img.size[0], 
							   src_img.size[1], 
							   GL_RGB, 
							   GL_UNSIGNED_BYTE, 
							   img_str )
		else:
			glTexImage2D( GL_TEXTURE_2D,    # target
            	          0,                # mipmap level
            	          3,                # color components (3: rgb, 4: rgba)
            	          src_img.size[0],  # texture width
            	          src_img.size[1],  # texture height
            	          0,                # border
            	          GL_RGB,           # format
        	              GL_UNSIGNED_BYTE, # data type
            	          img_str )         # texture data
		# return handle id
		return int(img_id)


#================================================================[ World Class ]

class World:

	#-------------------------------------------------------------------[ init ]

	def __init__( self, control ):

		# components
		self.__walls__        = []
		self.__ctrl__         = control
		self.__display_list__ = None
		self.__textures__     = Textures()

		self.__textures__.sketch_color[0] = self.__ctrl__.color_sketch_default

		# construct world
		self.__constructWorld__( control )

		# optional obstacles
		if len(control.obstacles) != 0:
			for i, o in enumerate(control.obstacles):
				self.__addObstacleWalls__( o, control.boxmix, i%len(self.__textures__.crate) )

		# find world limits [x_min, y_min, x_max, y_max]
		control.limits = numpy.array([numpy.iinfo('i').max,numpy.iinfo('i').max,numpy.iinfo('i').min,numpy.iinfo('i').min])
		for w in self.__walls__:
			control.limits[0] = min( w.vec_to[0], w.vec_from[0], control.limits[0] )
			control.limits[1] = min( w.vec_to[1], w.vec_from[1], control.limits[1] )
			control.limits[2] = max( w.vec_to[0], w.vec_from[0], control.limits[2] )
			control.limits[3] = max( w.vec_to[1], w.vec_from[1], control.limits[3] )

		# construct display list
		self.__constructDisplayList__()

	#-----------------------------------------------------------[ construction ]

	def __constructWorld__( self, control ):

		# build rectangular world ( dim := [ <world_length>, <world_width>, <world_height> ] )
		if control.type == 'box':
			self.__walls__.append( Wall( numpy.array([           0.0,           0.0]), numpy.array([           0.0,control.dim[1]]), control.dim[2], self.__textures__.wall[3 if control.wallmix else 0], control.wall_offset ) )
			self.__walls__.append( Wall( numpy.array([           0.0,control.dim[1]]), numpy.array([control.dim[0],control.dim[1]]), control.dim[2], self.__textures__.wall[0 if control.wallmix else 0], control.wall_offset ) )
			self.__walls__.append( Wall( numpy.array([control.dim[0],control.dim[1]]), numpy.array([control.dim[0],           0.0]), control.dim[2], self.__textures__.wall[1 if control.wallmix else 0], control.wall_offset ) )
			self.__walls__.append( Wall( numpy.array([control.dim[0],           0.0]), numpy.array([           0.0,           0.0]), control.dim[2], self.__textures__.wall[2 if control.wallmix else 0], control.wall_offset ) )

		# build star maze ( dim := [ <arms>, <arm_width>, <arm_length>, <arm_height> ] )
		elif control.type == 'star':
			# constants
			RAD2DEG = 180.0/math.pi
			DEG2RAD = math.pi/180.0
			# angles
			arm_dir  = 270.0
			dir_step = 360.0 / control.dim[0]
			inner_r  = control.dim[1] / (2*math.sin( (180.0/control.dim[0])*DEG2RAD ))
			# add arm walls
			for n in range(0,int(control.dim[0])):
				# arm vertices
				a = numpy.array([inner_r*math.cos((arm_dir-0.5*dir_step)*DEG2RAD), \
							  	 inner_r*math.sin((arm_dir-0.5*dir_step)*DEG2RAD)] )
				b = numpy.array([inner_r*math.cos((arm_dir-0.5*dir_step)*DEG2RAD) + math.cos(arm_dir*DEG2RAD)*control.dim[2], \
							  	 inner_r*math.sin((arm_dir-0.5*dir_step)*DEG2RAD) + math.sin(arm_dir*DEG2RAD)*control.dim[2]] )
				c = numpy.array([inner_r*math.cos((arm_dir+0.5*dir_step)*DEG2RAD), \
							  	 inner_r*math.sin((arm_dir+0.5*dir_step)*DEG2RAD)] )
				d = numpy.array([inner_r*math.cos((arm_dir+0.5*dir_step)*DEG2RAD) + math.cos(arm_dir*DEG2RAD)*control.dim[2], \
							  	 inner_r*math.sin((arm_dir+0.5*dir_step)*DEG2RAD) + math.sin(arm_dir*DEG2RAD)*control.dim[2]] )
				# arm walls (note: each complete arm gets a different texture in case of wallmix)
				self.__walls__.append( Wall( c, d, control.dim[3], self.__textures__.wall[0 if not control.wallmix else n%len(self.__textures__.wall)], control.wall_offset ) )
				self.__walls__.append( Wall( d, b, control.dim[3], self.__textures__.wall[0 if not control.wallmix else n%len(self.__textures__.wall)], control.wall_offset ) )
				self.__walls__.append( Wall( b, a, control.dim[3], self.__textures__.wall[0 if not control.wallmix else n%len(self.__textures__.wall)], control.wall_offset ) )
				# next
				arm_dir += dir_step
				if arm_dir >= 360: arm_dir -=360

		# build T maze ( dim := [ <vertical_length>, <vertical_width>, <horizontal_length>, <horizontal_width>, <wall_height> ] )
		elif control.type == 'T':
			# T coords
			a = numpy.array([-control.dim[1]/2.0, 0.0])
			b = numpy.array([-control.dim[1]/2.0, control.dim[0]])
			c = numpy.array([-control.dim[2]/2.0, control.dim[0]])
			d = numpy.array([-control.dim[2]/2.0, control.dim[0]+control.dim[3]])
			e = numpy.array([ control.dim[2]/2.0, control.dim[0]+control.dim[3]])
			f = numpy.array([ control.dim[2]/2.0, control.dim[0]])
			g = numpy.array([ control.dim[1]/2.0, control.dim[0]])
			h = numpy.array([ control.dim[1]/2.0, 0.0])
			# T walls
			self.__walls__.append( Wall( a, b, control.dim[4], self.__textures__.wall[0 if not control.wallmix else 0], control.wall_offset ) )
			self.__walls__.append( Wall( b, c, control.dim[4], self.__textures__.wall[0 if not control.wallmix else 1], control.wall_offset ) )
			self.__walls__.append( Wall( c, d, control.dim[4], self.__textures__.wall[0 if not control.wallmix else 2], control.wall_offset ) )
			self.__walls__.append( Wall( d, e, control.dim[4], self.__textures__.wall[0 if not control.wallmix else 3], control.wall_offset ) )
			self.__walls__.append( Wall( e, f, control.dim[4], self.__textures__.wall[0 if not control.wallmix else 0], control.wall_offset ) )
			self.__walls__.append( Wall( f, g, control.dim[4], self.__textures__.wall[0 if not control.wallmix else 1], control.wall_offset ) )
			self.__walls__.append( Wall( g, h, control.dim[4], self.__textures__.wall[0 if not control.wallmix else 2], control.wall_offset ) )
			self.__walls__.append( Wall( h, a, control.dim[4], self.__textures__.wall[0 if not control.wallmix else 3], control.wall_offset ) )

		# build circle maze ( dim := [ <radius>, <segments>, <wall_height> ] )
		elif control.type == 'circle':
			# constants
			RAD2DEG = 180.0/math.pi
			DEG2RAD = math.pi/180.0
			# angles
			angle = 0.0
			step  = 360.0 / control.dim[1]
			# circle segments
			for w in range(0,int(control.dim[1])):
				a = numpy.array([control.dim[0]*math.cos(angle*DEG2RAD),control.dim[0]*math.sin(angle*DEG2RAD)])
				b = numpy.array([control.dim[0]*math.cos((angle+step)*DEG2RAD),control.dim[0]*math.sin((angle+step)*DEG2RAD)])
				self.__walls__.append( Wall( b, a, control.dim[2], self.__textures__.wall[0 if not control.wallmix else int( w/(control.dim[1]/len(self.__textures__.wall)) )], control.wall_offset ) )
				angle += step
	
		# build world from file ( dim := [ <file_name> ] )
		elif control.type == 'file':
			# open file
			print('Reading custom world from \'%s\'.' % ('./current_experiment/'+control.dim[0]))
			world_file = open( './current_experiment/' + control.dim )
			# read lines
			for l in world_file:
				if l == '\n': break
				par = l.split()
				print(par)
				if par[0] == 'floor': self.__textures__.floor[0] = self.__textures__.index[par[1]]
				else:
					self.__walls__.append( Wall( numpy.array([float(par[0]),float(par[1])]), numpy.array([float(par[2]),float(par[3])]), def_CUSTOM_HEIGHT,  self.__textures__.index[par[4]], self.__ctrl__.wall_offset ) ) #self.__textures__.wall[int(par[4])], self.__ctrl__.wall_offset ) )

	def __addObstacleWalls__( self, obstacle, boxmix=False, index=0 ):
			self.__walls__.append( Wall( numpy.array([obstacle[0],obstacle[3]]), numpy.array([obstacle[0],obstacle[1]]), self.__ctrl__.box_dim[2], self.__textures__.crate[0 if not boxmix else index], self.__ctrl__.wall_offset ) )
			self.__walls__.append( Wall( numpy.array([obstacle[2],obstacle[3]]), numpy.array([obstacle[0],obstacle[3]]), self.__ctrl__.box_dim[2], self.__textures__.crate[0 if not boxmix else index], self.__ctrl__.wall_offset ) )
			self.__walls__.append( Wall( numpy.array([obstacle[2],obstacle[1]]), numpy.array([obstacle[2],obstacle[3]]), self.__ctrl__.box_dim[2], self.__textures__.crate[0 if not boxmix else index], self.__ctrl__.wall_offset ) )
			self.__walls__.append( Wall( numpy.array([obstacle[0],obstacle[1]]), numpy.array([obstacle[2],obstacle[1]]), self.__ctrl__.box_dim[2], self.__textures__.crate[0 if not boxmix else index], self.__ctrl__.wall_offset ) )

	def __constructDisplayList__( self ):
		# sort wall list by texture id
		self.__walls__ = sorted( self.__walls__, key = lambda wall: wall.texture )
		# start dispaly list
		self.__display_list__ = glGenLists(1)
		glNewList( self.__display_list__, GL_COMPILE )
		# floor quad
		l = self.__ctrl__.limits
		tex_id = self.__textures__.floor[0]
		glBindTexture( GL_TEXTURE_2D, tex_id )
		glBegin( GL_QUADS )
		glTexCoord2f( 0.0, 0.0 )
		glVertex3f( l[0], l[1], 0.0 )
		glTexCoord2f( 1.0, 0.0 )
		glVertex3f( l[2], l[1], 0.0 )
		glTexCoord2f( 1.0, 1.0 )
		glVertex3f( l[2], l[3], 0.0 )
		glTexCoord2f( 0.0, 1.0 )
		glVertex3f( l[0], l[3], 0.0 )
		# wall segments
		for w in self.__walls__:
			# change texture
			if w.texture != tex_id:
				glEnd()
				glBindTexture( GL_TEXTURE_2D, w.texture )
				glBegin( GL_QUADS )
			# wall segment quad
			glTexCoord2f( 0.0, 0.0 )
			glVertex3f( w.vec_from[0], w.vec_from[1], 0.0 )
			glTexCoord2f( 1.0, 0.0 )
			glVertex3f( w.vec_to[0], w.vec_to[1], 0.0 )
			glTexCoord2f( 1.0, 1.0 )
			glVertex3f( w.vec_to[0], w.vec_to[1], w.height )
			glTexCoord2f( 0.0, 1.0 )
			glVertex3f( w.vec_from[0], w.vec_from[1], w.height )
		# finish list
		glEnd()				
		glEndList()

	#--------------------------------------------------------------[ Utilities ]

	def validStep( self, pos_old, pos_new ):
		# check 1: new position still lies in the valid region
		if self.validPosition( pos_new ) == False:
			return False
		# check 2: step does not cross any wall segments
		for w in self.__walls__:
			if w.crossedBy( pos_old, pos_new):
				return False
		return True

	def validPosition( self, pos ):
		odd_nodes = False
		for w in self.__walls__:
			# break if too close to any wall
			if w.proximityAlert(pos): return False
			# run Point in Polygon algorithm (@ http://alienryderflex.com/polygon/)
			if w.vec_from[1]<pos[1] and w.vec_to[1]>=pos[1] or w.vec_to[1]<pos[1] and w.vec_from[1]>=pos[1]:
				if (w.vec_from[0]+(pos[1]-w.vec_from[1])/(w.vec_to[1]-w.vec_from[1])*(w.vec_to[0]-w.vec_from[0]) < pos[0]):
					odd_nodes = not odd_nodes
		return odd_nodes

	def randomPosition( self ):
		# init
		position = numpy.array( [0.0,0.0] )
		check    = False
		# find
		while check == False:
			position = numpy.array( [rnd.randrange(self.__ctrl__.limits[0],self.__ctrl__.limits[2]), \
		                          rnd.randrange(self.__ctrl__.limits[1],self.__ctrl__.limits[3])] )
			check = self.validPosition( position )
		# return
		return position

	#----------------------------------------------------------------[ Drawing ]

	def drawWorld( self, focus ):

		# office background (geometry, no skybox)
		glBindTexture( GL_TEXTURE_2D, self.__textures__.skybox )
		glBegin( GL_QUADS )	

		glTexCoord2f( 0.0, 0.0 )
		glVertex3f( -300.0, -300.0, 300.0 )
		glTexCoord2f( 0.33, 0.0 )
		glVertex3f(  300.0, -300.0, 300.0 )
		glTexCoord2f( 0.33, 0.33 )
		glVertex3f(  300.0, -300.0, 0.0 )
		glTexCoord2f( 0.0, 0.33 )
		glVertex3f( -300.0, -300.0, 0.0 )

		glTexCoord2f( 0.33, 0.0 )
		glVertex3f( -300.0, 300.0, 0.0 )
		glTexCoord2f( 0.66, 0.0 )
		glVertex3f(  300.0, 300.0, 0.0 )
		glTexCoord2f( 0.66, 0.33 )
		glVertex3f(  300.0, 300.0, 300.0 )
		glTexCoord2f( 0.33, 0.33 )
		glVertex3f( -300.0, 300.0, 300.0 )

		glTexCoord2f( 0.33, 0.33 )
		glVertex3f( -300.0, -300.0, 0.0 )
		glTexCoord2f( 0.66, 0.33 )
		glVertex3f( -300.0,  300.0, 0.0 )
		glTexCoord2f( 0.66, 0.66 )
		glVertex3f( -300.0,  300.0, 300.0 )
		glTexCoord2f( 0.33, 0.66 )
		glVertex3f( -300.0, -300.0, 300.0 )

		glTexCoord2f( 0.0, 0.33 )
		glVertex3f( 300.0, -300.0, 300.0 )
		glTexCoord2f( 0.33, 0.33 )
		glVertex3f( 300.0,  300.0, 300.0 )
		glTexCoord2f( 0.33, 0.66 )
		glVertex3f( 300.0,  300.0, 0.0 )
		glTexCoord2f( 0.0, 0.66 )
		glVertex3f( 300.0, -300.0, 0.0 )

		glTexCoord2f( 0.66, 0.5 ) # ceiling
		glVertex3f( -300.0, -300.0, 300.0 )
		glTexCoord2f( 1.0, 0.5 )
		glVertex3f( -300.0, 300.0, 300.0 )
		glTexCoord2f( 1.0, 1.0 )
		glVertex3f( 300.0, 300.0, 300.0 )
		glTexCoord2f( 0.66, 1.0 )
		glVertex3f( 300.0, -300.0, 300.0 )

		glEnd()

		# rat maze display list
		glCallList( self.__display_list__ )

	#--------------------------------------------------------------[ Sketching ]

	def sketchWorld( self, sketch_info=False, sketch_uniform=False, raster=False ):
		# walls
		for w in self.__walls__:
			glColor( self.__textures__.sketch_color[w.texture if self.__ctrl__.wallmix and not sketch_uniform else 0] )
			glBegin( GL_LINES )
			glVertex3f( w.vec_from[0], w.vec_from[1], def_MARKER_HEIGHT )
			glVertex3f( w.vec_to[0],   w.vec_to[1],   def_MARKER_HEIGHT )
			glEnd()
		# info: mark wall corners and show wall normals
		if sketch_info == True:
			# vertice marker (left corner each wall)
			for w in self.__walls__:
				self.sketchMarker( w.vec_from[0], w.vec_from[1] )
			# wall normals
			glColor( 0.8, 0.0, 0.0 )
			glBegin( GL_LINES )
			for w in self.__walls__:
				w_center = w.vec_from+0.5*(w.vec_to-w.vec_from)
				glVertex3f( w_center[0], w_center[1], def_MARKER_HEIGHT )
				glVertex3f( w_center[0]+w.normal[0]*5, w_center[1]+w.normal[1]*5, def_MARKER_HEIGHT )
			glEnd()
		# add raster overlay
		if raster == True:
			l = self.__ctrl__.limits
			# raster lines
			glLineWidth(1)
			glColor( 0.3, 0.3, 0.3 )
			glBegin( GL_LINES )
			for x in range(l[0],l[2],10):
				glVertex3f( float(x), l[1], def_MARKER_HEIGHT )
				glVertex3f( float(x), l[3], def_MARKER_HEIGHT )
			for y in range(l[1],l[3],10):
				glVertex3f( l[0], float(y), def_MARKER_HEIGHT )
				glVertex3f( l[2], float(y), def_MARKER_HEIGHT )
			glEnd()
			glColor( 1.0, 1.0, 1.0 )
			glBegin( GL_LINES )
			for x in range(l[0],l[2],50):
				glVertex3f( float(x), l[1], def_MARKER_HEIGHT )
				glVertex3f( float(x), l[3], def_MARKER_HEIGHT )
			for y in range(l[1],l[3],50):
				glVertex3f( l[0], float(y), def_MARKER_HEIGHT )
				glVertex3f( l[2], float(y), def_MARKER_HEIGHT )
			glEnd()
			# raster scale
			glColor( 0.0, 1.0, 0.0 )
			glLineWidth(2)
			glBegin( GL_LINES )
			glVertex3f( l[0]-(l[2]-l[0]), 0.0, def_MARKER_HEIGHT )
			glVertex3f( l[2]+(l[2]-l[0]), 0.0, def_MARKER_HEIGHT )
			glVertex3f( 0.0, l[1]-(l[3]-l[1]), def_MARKER_HEIGHT )
			glVertex3f( 0.0, l[3]+(l[3]-l[1]), def_MARKER_HEIGHT )
			glEnd()
			glLineWidth(1)
			for x in range(l[0],l[2],10):
				if x%50 == 0: drawNumber( x, (x,l[1]-10) )
			for y in range(l[1],l[3],10):
				if y%50 == 0: drawNumber( y, (l[0]-5*len(str(y)),y) )

	def sketchPath( self, path ):
		glColor( self.__ctrl__.color_rat_path )
		glBegin( GL_POINTS )
		for p in path:
			glVertex3f( p[0], p[1], def_MARKER_HEIGHT )
		glEnd()

	def sketchArrow( self, pos_x, pos_y, dir_x, dir_y, color=None ):
		# color
		if color == None:
			glColor( 0.6, 0.0, 0.0 )
		elif color == 'red':
			glColor( 0.8, 0.0, 0.0 )
		elif color == 'green':
			glColor( 0.0, 0.6, 0.0 )
		elif color == 'blue':
			glColor( 0.0, 0.0, 0.8 )
		elif color == 'grey':
			glColor( 0.4, 0.4, 0.4 )
		# normalized direction x2
		dir_xn = (dir_x / numpy.sqrt(dir_x**2+dir_y**2))*2.0
		dir_yn = (dir_y / numpy.sqrt(dir_x**2+dir_y**2))*2.0
		# draw
		glBegin( GL_LINES )
		glVertex3f( pos_x+dir_xn*3.0, pos_y+dir_yn*3.0, def_MARKER_HEIGHT )
		glVertex3f( pos_x+dir_yn, pos_y-dir_xn, def_MARKER_HEIGHT )
		glVertex3f( pos_x+dir_yn, pos_y-dir_xn, def_MARKER_HEIGHT )
		glVertex3f( pos_x-dir_yn, pos_y+dir_xn, def_MARKER_HEIGHT )		
		glVertex3f( pos_x-dir_yn, pos_y+dir_xn, def_MARKER_HEIGHT )		
		glVertex3f( pos_x+dir_xn*3.0, pos_y+dir_yn*3.0, def_MARKER_HEIGHT )
		glVertex3f( pos_x, pos_y, def_MARKER_HEIGHT )
		glVertex3f( pos_x-dir_xn*2.0, pos_y-dir_yn*2.0, def_MARKER_HEIGHT )
		glEnd()

	def sketchMarker( self, pos_x, pos_y, size=None, color=None ):
		"""
		utility function: Draw a simple marker within the simulation world.
		"""
		# size
		scale = 2.5
		if size == 'small': scale = 0.5
		# color
		glColor( self.__ctrl__.color_rat_marker )
		# draw
		glBegin( GL_LINES )
		glVertex3f( pos_x-scale, pos_y, def_MARKER_HEIGHT )
		glVertex3f( pos_x+scale, pos_y, def_MARKER_HEIGHT )
		glVertex3f( pos_x, pos_y-scale, def_MARKER_HEIGHT )
		glVertex3f( pos_x, pos_y+scale, def_MARKER_HEIGHT )
		glVertex3f( pos_x, pos_y, def_MARKER_HEIGHT-scale )
		glVertex3f( pos_x, pos_y, def_MARKER_HEIGHT+scale )
		glEnd()

