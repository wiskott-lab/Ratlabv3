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
import sys

# math
import math
import numpy  as np
import random as rnd

# OpenGL
from OpenGL.GLUT import *
from OpenGL.GLU  import *
from OpenGL.GL   import *

# utilities / own
import freezeable
Freezeable = freezeable.Freezeable

#------------------------------------------------------------------[ Constants ]

def_RAD2DEG         = 180.0/math.pi
def_DEG2RAD         = math.pi/180.0

#------------------------------------------------------------------[ Numpy Mod ]

np.seterr(divide='ignore') # ignore 'division by zero' errors (occur on path reset)


#==============================================================[ RatBot Class ]

class RatBot( Freezeable ):
	"""
	Class to set up and control a virtual rodend.
	"""

	#----------------------------------------------------------[ Construction ]

	def __init__( self, pos, control ):
		"""
		Constructor. Initializes the rat bot.
		pos    : Valid 2D position within the simulation world.
		control: Simulation control panel. Defined in ratlab.py.
		"""
		rnd.seed()
		# simulation control panel
		self.__ctrl__ = control
		# path
		self.__path__ = []
		self.__path__.append( pos )
		# follow path if specified via file
		if control.setup.rat.path != None:
			f = open( './current_experiment/' + control.setup.rat.path )
			control.setup.rat.path = np.zeros( [sum(1 for l in f),2] )
			f.seek(0)
			for i,l in enumerate(f):
				c = l.split()
				control.setup.rat.path[i] = np.array([c[0],c[1]])
			self.__path_index__ = 1
			# reset starting position
			self.__path__[0] = control.setup.rat.path[0]
		# lockdown
		self.freeze()

	#-----------------------------------------------------------[ Path Control ]

	def getPath( self ):
		"""
		Retrieve the rat's path data so far. The function returns an array of 2D
		positions.
		"""
		return self.__path__

	def __gaussianWhiteNoise2D__( self, dir=None ):
		# random unrestricted direction
		if dir is None or self.__ctrl__.setup.rat.arc == 360.0:
			angle = (rnd.random()*360.0) * def_DEG2RAD
			return np.array( [math.cos(angle),math.sin(angle)] )
		# random direction focused around given velocity vector
		else:
			try:
				dir_n = dir / math.sqrt( dir[0]**2+dir[1]**2 )
				dir_a = math.asin( abs(dir_n[1]) ) * def_RAD2DEG
				if   dir_n[0]<=0 and dir_n[1]>=0: dir_a =180.0-dir_a
				elif dir_n[0]<=0 and dir_n[1]<=0: dir_a =180.0+dir_a
				elif dir_n[0]>=0 and dir_n[1]<=0: dir_a =360.0-dir_a
				rat_fov = self.__ctrl__.setup.rat.arc
				angle   = (dir_a-rat_fov/2.0 + rnd.random()*rat_fov) * def_DEG2RAD
				return np.array( [math.cos(angle),math.sin(angle)] )
			except ValueError:
			#random rebound in case the path gets stuck in a corner
				return self.__gaussianWhiteNoise2D__()
           
	def followPathNodes( self ):
		# switch to next nav point when necessary
		path = self.__ctrl__.setup.rat.path
		pos  = self.__path__[ len(self.__path__)-1 ]
		dist = np.sqrt(np.vdot(pos-path[self.__path_index__],pos-path[self.__path_index__]))
		if dist < self.__ctrl__.setup.rat.speed:
			self.__path_index__ += 1
			self.__path_index__ %= len(path)
			# end of non-loop path: teleport back to starting position
			if self.__path_index__ == 0 and self.__ctrl__.setup.rat.path_loop == False:
				pos_next    = path[0]
				trajectory  = np.array( path[1]-path[0], dtype=np.float32 )
				trajectory /= np.sqrt( np.vdot(trajectory,trajectory) )
				self.__path__.append( pos_next )
				return (pos_next, trajectory)
		# new step
		step  = np.array( path[self.__path_index__]-pos, dtype=np.float32 )
		step /= np.sqrt(np.vdot(step,step))
		noise = self.__ctrl__.setup.rat.path_dev
		while True:
			if np.random.random() > 0.5:
				step += np.array( [-step[1],step[0]] )*noise
			else:
				step += np.array( [step[1],-step[0]] )*noise
			step *= self.__ctrl__.setup.rat.speed
			# check for valid step
			pos_next = pos + step
			#if self.__ctrl__.modules.world.validStep( pos, pos_next ) == True:
			self.__path__.append( pos_next )
			return (pos_next, step)
			#else:
			#	noise *= 0.5

	def nextPathStep( self ):
		"""
		Generate the next step of the rat's movement.
		"""
		# following a path?
		if self.__ctrl__.setup.rat.path is not None:
			return self.followPathNodes()
		# current position & velocity/direction
		pos      = self.__path__[len(self.__path__)-1]
		pos_next = np.array([np.nan,np.nan])
		if len(self.__path__) > 1: vel = pos-self.__path__[len(self.__path__)-2]
		else: vel = self.__gaussianWhiteNoise2D__()
		# generate next step
		while True:
			noise = self.__gaussianWhiteNoise2D__(vel)
			mom   = self.__ctrl__.setup.rat.path_mom
			step  = vel*mom + noise*(1.0-mom)
			step /= np.sqrt(np.vdot(step,step))
			step *= self.__ctrl__.setup.rat.speed
			# optional movement bias
			bias  = self.__ctrl__.setup.rat.bias
			step += bias*(np.dot(bias,step)**2)*np.sign(np.dot(bias,step))*self.__ctrl__.setup.rat.bias_s
			# check for valid step
			pos_next = pos + step
			if self.__ctrl__.modules.world.validStep( pos, pos_next ) == False: vel *= 0.5
			else: break
		# set and confirm
		self.__path__.append(pos_next)
		return (pos_next, pos_next-pos)

		if False: ##########################################################################################OLD RULES
			# current position and velocity																   ##########
			vel      = None																							#
			pos      = self.__path__[ len(self.__path__)-1 ]														#
			pos_next = np.array( [0.0,0.0] )       																	#
			if len( self.__path__ ) == 1:																			#
				vel = self.__gaussianWhiteNoise2D__()																#
			else:																									#
				vel = pos - self.__path__[ len(self.__path__)-2 ]													#
			vel *= self.__ctrl__.setup.rat.speed																	#
			# next step																								#
			check = False																							#
			pos_next = np.array( [0.0,0.0] )																		#
			while check == False:																					#
				# random path variation (rummaging behavior)														#
				noise = self.__gaussianWhiteNoise2D__( vel )														#
				# step width according to momentum term																#
				momentum = self.__ctrl__.setup.rat.path_mom															#
				step     = vel*momentum + noise*(1.0-momentum)														#
				# step modified by optional movement bias															#
				step_n = step/(math.sqrt(step[0]**2+step[1]**2))													#
				bias   = self.__ctrl__.setup.rat.bias																#
				step  += bias*(np.dot(bias,step_n)**2)*np.sign(np.dot(bias,step_n))*self.__ctrl__.setup.rat.bias_s	#
				# add up position & check for validity																#
				pos_next = pos + step																				#
				check = self.__ctrl__.modules.world.validStep( pos, pos_next )										#
				if check == False:																					#
					vel *= 0.5																						#
			vel = pos_next - pos																					#
			pos = pos_next																							#
			self.__path__.append( pos )																				#
			# return generated state in the format ( [pos_x,pos_y], [vel_x,vel_y] )									#
			return (pos, vel)																						#
		#############################################################################################################
