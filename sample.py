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


#=====================================================================[ Header ]

# system
import os
import sys
import time
import types
import struct
import pickle

# math
import numpy
import math
import mdp

print('Running MDP version', mdp.__version__) # , mdp.config.has_mdp, 'from', mdp.__file__

# graphics
from PIL import Image 	  as IMG
from PIL import ImageDraw as IMG_DRW
from OpenGL.GLUT import *
from OpenGL.GLU  import *
from OpenGL.GL   import *

# ratlab modules
sys.path.append( './util' )
from util.setup import *
import world as WORLD

#--------------------------------------------------------------------[ Control ]

class LocalControl( Freezeable ):
	def __init__( self ):

		self.defines = EmptyOptionContainer()			# defines
		self.defines.window_title  = 'RatLab Sampling Program'
		self.defines.window_width  = None
		self.defines.window_height = None
		self.defines.freeze()

		self.cfg = EmptyOptionContainer()				# config
		self.cfg.file_prefix   = ''
		self.cfg.setup_file    = 'exp_setup'
		self.cfg.sfa_network   = None
		self.cfg.sample_order  = None
		self.cfg.verbose       = False
		# spatial sampling
		self.cfg.sample_dir    = [] 
		self.cfg.sample_period = None
		# directional sampling
		self.cfg.sample_pos   = None
		self.cfg.freeze()

		self.state = EmptyOptionContainer()			# state
		self.state.sample_data = []
		self.state.freeze()

		self.setup     = None								# global setup
		self.world     = None								# world instance

ctrl = LocalControl()


#==================================================================[ Utilities ]

def colorScale_HotCold( value, limit_min, limit_max ):
	# move value and [min;max] range to [0;max'] range
	value     -= limit_min
	limit_max -= limit_min
	# get 1024 resolution scale
	rgb = numpy.array([0,0,0])
	y = int( (value*1024.0)/limit_max )
	# convert to blue-to-red color trace
	if y < 256:
		rgb[1] = y
		rgb[2] = 255
	elif y < 512:
		rgb[1] = 255
		rgb[2] = 512-(y+1)
	elif y < 768:
		rgb[0] = y-512
		rgb[1] = 255
	else:
		rgb[0] = 255
		rgb[1] = 1024-(y+1)
	# return RGBA color tuple
	return (rgb[0],rgb[1],rgb[2],255)

def colorScale_Jet( value, val_min, val_max ):
	# move range from [min,max] to [0,max']
	value   -= val_min
	val_max -= val_min
	# scale value from [0,max'] to [0,4]
	value = (value*4.0)/val_max
	# color array
	rgb = numpy.array([0,0,0])
	# jet scale
	if( value <= 0.5 ):
		rgb[2] = 128 + value*255
	elif( value <= 1.5 ):
		rgb[1] = (value-0.5)*255
		rgb[2] = 255
	elif( value <= 2.5 ):
		rgb[0] = (value-1.5)*255
		rgb[1] = 255
		rgb[2] = 255 - (value-1.5)*255
	elif( value <= 3.5 ):
		rgb[0] = 255
		rgb[1] = 255 - (value-2.5)*255
	else:
		rgb[0] = 255 - (value-3.5)*255
	# return RGBA color tuple
	return (rgb[0],rgb[1],rgb[2],255)

def colorScale_ZA( value, val_min, val_max, zero_level=120, scalar_only=False ): # ZA: zero align (preset zero_level in [0,1024])
	# checks
	if val_max <= val_min: return (255,0,255,255) if scalar_only==False else -1.0	# ERR
	if value   >  val_max: return (128,0,0,255)   if scalar_only==False else 1024	# pos cutoff
	if value   <  val_min: return (0,0,128,255)   if scalar_only==False else  0.0	# neg cutoff
	# setup
	pos_scale    = 1024.0-zero_level
	scale_factor = pos_scale/val_max
	scale_value  = zero_level + (value*scale_factor)
	if scalar_only == True: return int(scale_value if scale_value >= 0 else 0)
	# cutoff smaller values
	if scale_value < 0: return (0,0,0,255)
	# scale value to RGB color
	rgb = numpy.array([0,0,0])
	if( scale_value < 128 ):
		rgb[2] = 128 + scale_value
	elif( scale_value < 384 ):
		rgb[1] = scale_value-128
		rgb[2] = 255
	elif( scale_value < 640.0 ):
		rgb[0] = scale_value-384
		rgb[1] = 255
		rgb[2] = 255 - (scale_value-384)
	elif( scale_value < 896 ):
		rgb[0] = 255
		rgb[1] = 255 - (scale_value-640)
	elif( scale_value <= 1024 ):
		rgb[0] = 255 - (scale_value-896)
	else:
		return (255,255,255,255) ### ERR
	# return RGBA color tuble
	return (rgb[0],rgb[1],rgb[2],255)

def createMap():
	# world limits
	dim_x = abs( ctrl.setup.world.limits[0] - ctrl.setup.world.limits[2] )
	dim_y = abs( ctrl.setup.world.limits[1] - ctrl.setup.world.limits[3] )
	# image
	map_img = IMG.new( 'RGB', (dim_x,dim_y) )
	map_dat = map_img.load()
	# loop through valid positions & print map
	i = 0
	for y in range(dim_y):
		for x in range(dim_x):
			if( ctrl.world.validPosition((ctrl.setup.world.limits[0]+x,ctrl.setup.world.limits[1]+y)) ):
				map_dat[x,y] = (0,0,0)
			else:
				map_dat[x,y] = (128,128,128)
			i+=1
			print('\rConstructing map: %d' % ((i*100)/(dim_x*dim_y)), '%')
	print('done.\nMap saved as file \'./current_experiment/exp_map.bmp\'')
	# flip image to fit image to screen coordinates & save
	map_img = map_img.transpose( IMG.FLIP_TOP_BOTTOM )
	map_img.save( './current_experiment/exp_map.png' )

def gridGenerator( param ):
	# absolute world dimensions
	dim_x = abs( ctrl.setup.world.limits[0] - ctrl.setup.world.limits[2] )
	dim_y = abs( ctrl.setup.world.limits[1] - ctrl.setup.world.limits[3] )
	# generate grid positions
	for y in range(0, dim_y, param):
		for x in range(0, dim_x, param):
			yield (int(ctrl.setup.world.limits[0]+x),int(ctrl.setup.world.limits[1]+y))

# needed by unpickled .tsa files that use custom expansions
def identity(x): return x
def exp(x): return (abs(x)**0.8) / ((x**2).sum(axis=1).reshape(-1,1) + 1)

#-------------------------------------------------------------------[ Graphics ]

def setupOpenGL( spatial=True ):
	
	# create GLUT window
	glutInit( sys.argv )
	glutInitDisplayMode( GLUT_DOUBLE |
		                 GLUT_RGBA   |
		                 GLUT_DEPTH  )
	glutInitWindowSize( ctrl.defines.window_width, ctrl.defines.window_height )
	glutCreateWindow( ctrl.defines.window_title )

	# set GLUT display function & timer
	if spatial:
		glutDisplayFunc( display_sampler_spatial )
	else:
		glutDisplayFunc( display_sampler_directional )
	glutTimerFunc( 1000//40, drawcall, 1 )

	# projection matrix setup w/ default viewport
	glViewport( 0, 0, ctrl.defines.window_width, ctrl.defines.window_height )

	glMatrixMode( GL_PROJECTION )
	glLoadIdentity()
	gluPerspective( ctrl.setup.rat.fov[1],
				    float(ctrl.defines.window_width) / float(ctrl.defines.window_height),
				    ctrl.setup.opengl.clip_near,
				    ctrl.setup.opengl.clip_far )

	# viewing matrix setup
	glMatrixMode( GL_MODELVIEW )
	glLoadIdentity()

	# misellaneous parameters
	glClearColor( 0.0, 0.0, 0.0, 0.0 )
	glLineWidth( 2 )
	glLineStipple( 1, 0xAAAA )

	# depth buffer
	glClearDepth( 1.0 )
	glEnable( GL_DEPTH_TEST )
	glDepthFunc( GL_LEQUAL )

	# backface culling
	glCullFace( GL_BACK )
	glEnable( GL_CULL_FACE )

	# texture mapping
	glEnable( GL_TEXTURE_2D )

def drawcall( i ):
    glutPostRedisplay()
    glutTimerFunc( 0, drawcall, 1 )


#====================================================================[ Sampler ]

def sample_spatial( args ):

	# get list of sampling directions from args
	for i, s in enumerate( args ):
		if s == 'all':
			ctrl.cfg.sample_dir.append( ('n', numpy.array([ 0, 1])) )
			ctrl.cfg.sample_dir.append( ('e', numpy.array([ 1, 0])) )
			ctrl.cfg.sample_dir.append( ('s', numpy.array([ 0,-1])) )
			ctrl.cfg.sample_dir.append( ('w', numpy.array([-1, 0])) )
			ctrl.cfg.sample_dir.append( ('ne', numpy.array([ numpy.sqrt(0.5), numpy.sqrt(0.5)])) )
			ctrl.cfg.sample_dir.append( ('se', numpy.array([ numpy.sqrt(0.5),-numpy.sqrt(0.5)])) )
			ctrl.cfg.sample_dir.append( ('sw', numpy.array([-numpy.sqrt(0.5),-numpy.sqrt(0.5)])) )
			ctrl.cfg.sample_dir.append( ('nw', numpy.array([-numpy.sqrt(0.5), numpy.sqrt(0.5)])) )

		elif s == 'n':	ctrl.cfg.sample_dir.append( (s, numpy.array([0,1])) )
		elif s == 'e':	ctrl.cfg.sample_dir.append( (s, numpy.array([1,0])) )
		elif s == 's':	ctrl.cfg.sample_dir.append( (s, numpy.array([0,-1])) )
		elif s == 'w':	ctrl.cfg.sample_dir.append( (s, numpy.array([-1,0])) )

		elif s == 'ne':	ctrl.cfg.sample_dir.append( (s, numpy.array([numpy.sqrt(0.5),numpy.sqrt(0.5)])) )
		elif s == 'se':	ctrl.cfg.sample_dir.append( (s, numpy.array([numpy.sqrt(0.5),-numpy.sqrt(0.5)])) )
		elif s == 'sw':	ctrl.cfg.sample_dir.append( (s, numpy.array([-numpy.sqrt(0.5),-numpy.sqrt(0.5)])) )
		elif s == 'nw':	ctrl.cfg.sample_dir.append( (s, numpy.array([-numpy.sqrt(0.5),numpy.sqrt(0.5)])) )

	if len(ctrl.cfg.sample_dir) == 0:
		print('Warning! No sampling directions!')
		return

	# start display loop for directional sampling 
	glutMainLoop()

def sample_directional( args ):

	# sample over grid positions
	if 'grid' in args:

		# create map file
		map_img = None
		try:
			map_img = IMG.open( './current_experiment/exp_map.png' )
			map_img = map_img.transpose( IMG.FLIP_TOP_BOTTOM )
		except: pass
		if map_img == None:
			createMap()
			map_img = IMG.open( './current_experiment/exp_map.png' )
			map_img = map_img.transpose( IMG.FLIP_TOP_BOTTOM )
		map_dat = map_img.load()

		# sampling grid positions
		grid = None
		for i, val in enumerate( args ):
			if val == 'grid': grid = gridGenerator( int(sys.argv[i+1]) )
	
		ctrl.cfg.sample_pos = []
		for i in grid:
			if ctrl.world.validPosition((i[0],i[1])):
				map_dat[i[0]-int(ctrl.setup.world.limits[0]),i[1]-int(ctrl.setup.world.limits[1])] = (255,0,0)
				ctrl.cfg.sample_pos.append( (i[0]-int(ctrl.setup.world.limits[0]),i[1]-int(ctrl.setup.world.limits[1])) )

		map_img = map_img.transpose( IMG.FLIP_TOP_BOTTOM )
		map_img.save( './current_experiment/exp_sample_grid.bmp' )
		print('Sample grid visualization stored to file \'./current_experiment/exp_sample_grid.bmp\'.')

	# sample over custom/manual positions
	else:
		map_img = None
		try:
			map_img = IMG.open( './current_experiment/exp_map.png' )
			map_img = map_img.transpose( IMG.FLIP_TOP_BOTTOM )
		except:
			print('Error! File \'./current_experiment/exp_map.png\' was not found.\nMake sure to create this file using the \'map\' parameter.')
			sys.exit()
		map_dat = map_img.load()

		ctrl.cfg.sample_pos = []
		for y in range( map_img.size[1] ):
			for x in range( map_img.size[0] ):
				if map_dat[x,y][0] == 255:
					ctrl.cfg.sample_pos.append( (ctrl.setup.world.limits[0]+x,ctrl.setup.world.limits[0]+y) )
		print('%d custom sampling positions found.' % len(ctrl.cfg.sample_pos))

	# start display loop for directional sampling 
	glutMainLoop()

#------------------------------------------------------------[ Spatial Sampler ]

def display_sampler_spatial():

	# sampling runs
	world_size_x = ctrl.setup.world.limits[2] - ctrl.setup.world.limits[0]
	world_size_y = ctrl.setup.world.limits[3] - ctrl.setup.world.limits[1]

	world_sample_size_x = int( world_size_x / ctrl.cfg.sample_period )
	world_sample_size_y = int( world_size_y / ctrl.cfg.sample_period )

	print('Sampling %d run(s); extracting the %d slowest signals.' % (len(ctrl.cfg.sample_dir), ctrl.cfg.sample_order))
	print('Using sampling period %d (%d position checks per sampling run)' % ( ctrl.cfg.sample_period, world_sample_size_x*world_sample_size_y ))

	sample_img  = IMG.new( 'RGBA', (world_sample_size_x,world_sample_size_y) )
	sample_data = sample_img.load()

	for r in range(0, len(ctrl.cfg.sample_dir)):

		# sampling data for next direction
		sample_data_raw = numpy.zeros( (ctrl.cfg.sample_order, world_sample_size_x, world_sample_size_y) )
		ctrl.state.sample_data.append( sample_data_raw )

		# direction angle
		dir_a = math.asin( abs(ctrl.cfg.sample_dir[r][1][1]) ) * ctrl.setup.constants.RAD2DEG
		if   ctrl.cfg.sample_dir[r][1][0]<=0 and ctrl.cfg.sample_dir[r][1][1]>=0: dir_a =180.0-dir_a
		elif ctrl.cfg.sample_dir[r][1][0]<=0 and ctrl.cfg.sample_dir[r][1][1]<=0: dir_a =180.0+dir_a
		elif ctrl.cfg.sample_dir[r][1][0]>=0 and ctrl.cfg.sample_dir[r][1][1]<=0: dir_a =360.0-dir_a

		# loop through positions
		ping  = time.time()
		pos_z = ctrl.setup.world.cam_height
		cnt   = 0.0

		limits = ctrl.setup.world.limits
		for pos_y in range(int(limits[1]),int(limits[3]),ctrl.cfg.sample_period):
			for pos_x in range(int(limits[0]),int(limits[2]),ctrl.cfg.sample_period):
				if ctrl.world.validPosition( numpy.array([pos_x,pos_y]) ):

					# render view
					glutSwapBuffers()
					glClear( GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT )
					glBindTexture( GL_TEXTURE_2D, 0 )

					x = 0
					for i in range( int(dir_a-ctrl.setup.rat.fov[0]/2), int(dir_a+ctrl.setup.rat.fov[0]/2) ):

						glViewport( x,0,1,int(ctrl.setup.rat.fov[1]) )

						glMatrixMode( GL_PROJECTION )
						glLoadIdentity()
						gluPerspective( ctrl.setup.rat.fov[1], 1.0/ctrl.setup.rat.fov[1], 
										ctrl.setup.opengl.clip_near, ctrl.setup.opengl.clip_far )

						glMatrixMode( GL_MODELVIEW )
						glLoadIdentity()

						focus = [ pos_x+math.cos(i*ctrl.setup.constants.DEG2RAD)*100.0,
								  pos_y+math.sin(i*ctrl.setup.constants.DEG2RAD)*100.0,
								  pos_z ]

						gluLookAt( pos_x, pos_y, pos_z,
								   focus[0], focus[1], focus[2], 
								   0,0,1 )

						ctrl.world.drawWorld( focus )
						x+=1
	
					# get frame data
					opengl_buffer  = glReadPixels( 0, 0, int(ctrl.setup.rat.fov[0]), int(ctrl.setup.rat.fov[1]), GL_RGBA, GL_UNSIGNED_BYTE )
					last_frame_img = IMG.frombuffer( 'RGBA', (int(ctrl.setup.rat.fov[0]),int(ctrl.setup.rat.fov[1])), opengl_buffer, 'raw', 'RGBA', 0, 0 )
					if ctrl.cfg.sfa_network[0].in_channel_dim == 1: last_frame_img = last_frame_img.convert( 'L' )
					frame_data = last_frame_img.load()

					data = None
					i=0
					if ctrl.setup.rat.color == 'RGB':
						data = numpy.zeros( (1,int(ctrl.setup.rat.fov[0])*int(ctrl.setup.rat.fov[1])*3), dtype=numpy.float32 ) # row-vector 'matrix'
						for y in range(0,int(ctrl.setup.rat.fov[1])):
							for x in range(0,int(ctrl.setup.rat.fov[0])):
								data[0,i]   = frame_data[x,y][0]
								data[0,i+1] = frame_data[x,y][1]
								data[0,i+2] = frame_data[x,y][2]
								i+=3
					else:
						data = numpy.zeros( (1,int(ctrl.setup.rat.fov[0])*int(ctrl.setup.rat.fov[1])), dtype=numpy.float32 ) # row-vector 'matrix'
						for y in range(0,int(ctrl.setup.rat.fov[1])):
							for x in range(0,int(ctrl.setup.rat.fov[0])):
								data[0,i] = frame_data[x,y]
								i+=1

					# get network value
					network_result = ctrl.cfg.sfa_network.execute( data )
					for k in range(0, ctrl.cfg.sample_order):
						sample_data_raw[k, (pos_x-ctrl.setup.world.limits[0])//ctrl.cfg.sample_period, (pos_y-ctrl.setup.world.limits[1])//ctrl.cfg.sample_period] = network_result[0,k]

				# mark invalid positions for blacking out as NAN
				else:
					for k in range(0, ctrl.cfg.sample_order):
						sample_data_raw[k, (pos_x-ctrl.setup.world.limits[0])//ctrl.cfg.sample_period, (pos_y-ctrl.setup.world.limits[1])//ctrl.cfg.sample_period] = numpy.NAN
							
				# update progress bar
				cnt += 1
				done = int( cnt/(world_sample_size_x*world_sample_size_y)*50.0 )
				sys.stdout.write( '\r' + '[SAMPLING][' + '='*done + '-'*(50-done) + ']~[' + '%d/%.2f' % (cnt,cnt/(world_sample_size_x*world_sample_size_y)*100.0) + '%]' )
				sys.stdout.flush()
		print('~[%dsec/%dmin]' % (time.time()-ping, (time.time()-ping)/60.0))

		# create local sampling data (i.e, scaled to local min/max values)
		for k in range(0, ctrl.cfg.sample_order):
			local_max = numpy.finfo('f').min
			local_min = numpy.finfo('f').max

			# find data range & update global sample range if neccesary
			for y in range(0,world_sample_size_y):
				for x in range(0,world_sample_size_x):
					if numpy.isnan( sample_data_raw[k,x,y] ):
						continue
					if sample_data_raw[k,x,y] > local_max:
						local_max = sample_data_raw[k,x,y]
					if sample_data_raw[k,x,y] < local_min:
						local_min = sample_data_raw[k,x,y]

			# polarize heuristic: largest value assumed to be positive
			sample_sign = 1
			if abs(local_min)>abs(local_max):
				tmp         = local_min
				local_min   = -local_max
				local_max   = -tmp
				sample_sign = -1

			# scale local response to color range
			sample_data_scaled = numpy.zeros([world_sample_size_x,world_sample_size_y])
			for y in range(0,world_sample_size_y):
				for x in range(0,world_sample_size_x):
					if numpy.isnan( sample_data_raw[k,x,y] ):
						sample_data[x,y]        = (0,0,0)
						sample_data_scaled[x,y] = 0
					else:
						sample_data[x,y]        = colorScale_ZA( sample_sign*sample_data_raw[k,x,y], local_min, local_max )
						sample_data_scaled[x,y] = colorScale_ZA( sample_sign*sample_data_raw[k,x,y], local_min, local_max, scalar_only=True )

			# write plots
			if ctrl.cfg.verbose:
				filename = ctrl.cfg.file_prefix + 'sample_' + str(k+1) + '_' + ctrl.cfg.sample_dir[r][0] + '['+str(local_min)+';'+str(local_max)+']' + '.png'
			else:
				filename = ctrl.cfg.file_prefix + 'sample_' + str(k+1) + '_' + ctrl.cfg.sample_dir[r][0] + '.png'
			sample_img.transpose(IMG.FLIP_TOP_BOTTOM).save( './current_experiment/sampling_plots/local/' + filename  )

			# write sample values
			filename = ctrl.cfg.file_prefix + 'sample_' + str(k+1) + '_' + ctrl.cfg.sample_dir[r][0] + '.txt'
			numpy.savetxt( './current_experiment/sampling_values_raw/local/'+filename, sample_data_raw[k]*sample_sign )
			numpy.savetxt( './current_experiment/sampling_values/local/'+filename,     sample_data_scaled )

	# average sampled activity over directions
	print('Averaging samples..')
	for k in range(ctrl.cfg.sample_order):

		# average activity of signal k at all sampled positions
		avg = numpy.zeros( (world_sample_size_x,world_sample_size_y) )
		for d, dir in enumerate(ctrl.cfg.sample_dir):
			avg += ctrl.state.sample_data[d][k]
		avg /= len(ctrl.cfg.sample_dir)

		# local scale and polarization
		sample_sign = 1
		local_max = numpy.nanmax( avg.flatten() )
		local_min = numpy.nanmin( avg.flatten() )
		if abs(local_min) > abs(local_max):
			tmp = local_min
			local_min   = -local_max	
			local_max   = -tmp
			sample_sign = -1
	
		# average plot
		sample_data_scaled = numpy.zeros([world_sample_size_x,world_sample_size_y])
		for y in range(0,world_sample_size_y):
			for x in range(0,world_sample_size_x):
				if numpy.isnan( avg[x,y] ):
					sample_data[x,y]        = (0,0,0)
					sample_data_scaled[x,y] = 0
				else:
					sample_data[x,y]        = colorScale_ZA( sample_sign*avg[x,y], local_min, local_max )
					sample_data_scaled[x,y] = colorScale_ZA( sample_sign*avg[x,y], local_min, local_max, scalar_only=True )
		
		# write plots
		if ctrl.cfg.verbose:
			filename = ctrl.cfg.file_prefix + 'avg_sample_' + str(k+1) + '['+str(local_min)+';'+str(local_max)+']' + '.png'
		else:
			filename = ctrl.cfg.file_prefix + 'avg_sample_' + str(k+1) + '.png'
		sample_img.transpose(IMG.FLIP_TOP_BOTTOM).save( './current_experiment/sampling_plots/average/' + filename  )

		# write sample values
		filename = ctrl.cfg.file_prefix + 'avg_sample_' + str(k+1) + '.png'
		numpy.savetxt( './current_experiment/sampling_values_raw/average/'+filename, avg*sample_sign )
		numpy.savetxt( './current_experiment/sampling_values/average/'+filename,     sample_data_scaled )

	print('done.')

	# all done
	os._exit(1)

#--------------------------------------------------------[ Directional Sampler ]

def display_sampler_directional():

	# complete sampling data
	sample_data     = numpy.zeros( (len(ctrl.cfg.sample_pos),360, ctrl.cfg.sample_order) )
	sample_data_avg = numpy.zeros( (360,ctrl.cfg.sample_order) )

	# loop over sampling positions
	ping = time.time()
	for p, pos in enumerate(ctrl.cfg.sample_pos):
	
		print('Sampling position %d of %d @ (%d,%d).' % (p+1,len(ctrl.cfg.sample_pos),pos[0],pos[1]))
	
		cnt = 0.0
		for dir_a in range(360):

			# render view
			glutSwapBuffers()
			glClear( GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT )
			glBindTexture( GL_TEXTURE_2D, 0 )

			x = 0
			for i in range( int(dir_a-ctrl.setup.rat.fov[0]/2), int(dir_a+ctrl.setup.rat.fov[0]/2) ):

				glViewport( x,0,1,int(ctrl.setup.rat.fov[1]) )

				glMatrixMode( GL_PROJECTION )
				glLoadIdentity()
				gluPerspective( ctrl.setup.rat.fov[1], 1.0/ctrl.setup.rat.fov[1], ctrl.setup.opengl.clip_near, ctrl.setup.opengl.clip_far )

				glMatrixMode( GL_MODELVIEW )
				glLoadIdentity()

				focus = [ pos[0]+math.cos(i*ctrl.setup.constants.DEG2RAD)*100.0,
						  pos[1]+math.sin(i*ctrl.setup.constants.DEG2RAD)*100.0,
						  ctrl.setup.world.cam_height ]

				gluLookAt( pos[0], pos[1], ctrl.setup.world.cam_height,
						   focus[0], focus[1], focus[2], 	
						   0,0,1 )

				ctrl.world.drawWorld( focus )
				x+=1

			# get frama data (color only atm)
			opengl_buffer  = glReadPixels( 0, 0, int(ctrl.setup.rat.fov[0]), int(ctrl.setup.rat.fov[1]), GL_RGBA, GL_UNSIGNED_BYTE )
			last_frame_img = IMG.frombuffer( 'RGBA', (int(ctrl.setup.rat.fov[0]),int(ctrl.setup.rat.fov[1])), opengl_buffer, 'raw', 'RGBA', 0, 0 )
			if ctrl.cfg.sfa_network[0].in_channel_dim == 1: last_frame_img = last_frame_img.convert( 'L' )
			frame_data = last_frame_img.load()

			data = None
			i=0
			if ctrl.setup.rat.color == 'RGB':
				data = numpy.zeros( (1,int(ctrl.setup.rat.fov[0])*int(ctrl.setup.rat.fov[1])*3), dtype=numpy.float32 ) # row-vector 'matrix'
				for y in range(0,int(ctrl.setup.rat.fov[1])):
					for x in range(0,int(ctrl.setup.rat.fov[0])):
						data[0,i]   = frame_data[x,y][0]
						data[0,i+1] = frame_data[x,y][1]
						data[0,i+2] = frame_data[x,y][2]
						i+=3
			else:
				data = numpy.zeros( (1,int(ctrl.setup.rat.fov[0])*int(ctrl.setup.rat.fov[1])), dtype=numpy.float32 ) # row-vector 'matrix'
				for y in range(0,int(ctrl.setup.rat.fov[1])):
					for x in range(0,int(ctrl.setup.rat.fov[0])):
						data[0,i] = frame_data[x,y]
						i+=1

			# get network value
			network_result = ctrl.cfg.sfa_network.execute( data )[:,:ctrl.cfg.sample_order]
			sample_data[p, dir_a] = network_result[0]

			# update progress bar
			cnt += 1
			done = int( cnt/360.0 *50.0 )
			sys.stdout.write( '\r' + '[SAMPLING][' + '='*done + '-'*(50-done) + ']~[' + '%d/%.2f' % (cnt, cnt/360.0*100.0) + '%]' )
			sys.stdout.flush()
		print('')

	print('Sampling time: %dsec ~ %dmin' % (time.time()-ping, (time.time()-ping)/60.0))

	# plot individual response for each position 
	for p, pos in enumerate(ctrl.cfg.sample_pos):

		print('Creating plot for position %d @ (%d,%d).' % (p+1,pos[0],pos[1]))

		for sig in range(ctrl.cfg.sample_order):

			# add individual set to global average
			sample_data_avg[:,sig] += sample_data[p,:,sig]

			# scale
			local_max = numpy.finfo('f').min
			local_min = numpy.finfo('f').max
			for a in range(360):
				if sample_data[p,a,sig] > local_max:
					local_max = sample_data[p,a,sig]
				if sample_data[p,a,sig] < local_min:
					local_min = sample_data[p,a,sig]

			# polarize
			sample_sign = 1
			if abs(local_min)>abs(local_max):
				tmp         = local_min
				local_min   = -local_max
				local_max   = -tmp
				sample_sign = -1
			
			# plot
			sample_img = IMG.new( 'RGBA', (200,200), 'white' )
			sample_pix = sample_img.load()
			sample_drw = IMG_DRW.Draw( sample_img )

			sample_drw.line( (100,0,100,199), fill=(200,200,200,255) )
			sample_drw.line( (0,100,199,100), fill=(200,200,200,255) )
			sample_drw.arc( (0,0,199,199), 0, 360, fill=(200,200,200,255) )

			for a in range(360):
				r = ((sample_sign*sample_data[p,a,sig]-local_min)*99.0) / (local_max-local_min)
				x = 100 + numpy.cos(a*ctrl.setup.constants.DEG2RAD) * r
				y = 100 + numpy.sin(a*ctrl.setup.constants.DEG2RAD) * r

				sample_drw.line( (100,100,x,y), fill=(0,0,0,255) )

				if r > 75:
					x = 100 + numpy.cos(a*ctrl.setup.constants.DEG2RAD) * 99
					y = 100 + numpy.sin(a*ctrl.setup.constants.DEG2RAD) * 99
					sample_pix[x,y] = (255,0,0,255)
					x = 100 + numpy.cos(a*ctrl.setup.constants.DEG2RAD) * 98
					y = 100 + numpy.sin(a*ctrl.setup.constants.DEG2RAD) * 98
					sample_pix[x,y] = (255,0,0,255)
					x = 100 + numpy.cos(a*ctrl.setup.constants.DEG2RAD) * 97
					y = 100 + numpy.sin(a*ctrl.setup.constants.DEG2RAD) * 97
					sample_pix[x,y] = (255,0,0,255)

			path = './current_experiment/sampling_rad/local/'
			sample_img.save( path + 'pos_' + str(p).zfill(3) + '_sig_' + str(sig).zfill(2) + '.png' )

	# plot average response over space
	sample_data_avg /= len(ctrl.cfg.sample_pos)

	for sig in range(ctrl.cfg.sample_order):

		# scale
		local_max = numpy.finfo('f').min
		local_min = numpy.finfo('f').max
		for a in range(360):
			if sample_data_avg[a,sig] > local_max:
				local_max = sample_data_avg[a,sig]
			if sample_data_avg[a,sig] < local_min:
				local_min = sample_data_avg[a,sig]

		# polarize
		sample_sign = 1
		if abs(local_min)>abs(local_max):
			tmp         = local_min
			local_min   = -local_max
			local_max   = -tmp
			sample_sign = -1

		# plot
		sample_img = IMG.new( 'RGBA', (200,200), 'white' )
		sample_pix = sample_img.load()
		sample_drw = IMG_DRW.Draw( sample_img )

		sample_drw.line( (100,0,100,199), fill=(200,200,200,255) )
		sample_drw.line( (0,100,199,100), fill=(200,200,200,255) )
		sample_drw.arc( (0,0,199,199), 0, 360, fill=(200,200,200,255) )

		for a in range(360):
			r = ((sample_sign*sample_data_avg[a,sig]-local_min)*99.0) / (local_max-local_min)
			x = 100 + numpy.cos(a*ctrl.setup.constants.DEG2RAD) * r
			y = 100 + numpy.sin(a*ctrl.setup.constants.DEG2RAD) * r

			sample_drw.line( (100,100,x,y), fill=(0,0,0,255) )

			if r > 75:
				x = 100 + numpy.cos(a*ctrl.setup.constants.DEG2RAD) * 99
				y = 100 + numpy.sin(a*ctrl.setup.constants.DEG2RAD) * 99
				sample_pix[x,y] = (255,0,0,255)
				x = 100 + numpy.cos(a*ctrl.setup.constants.DEG2RAD) * 98
				y = 100 + numpy.sin(a*ctrl.setup.constants.DEG2RAD) * 98
				sample_pix[x,y] = (255,0,0,255)
				x = 100 + numpy.cos(a*ctrl.setup.constants.DEG2RAD) * 97
				y = 100 + numpy.sin(a*ctrl.setup.constants.DEG2RAD) * 97
				sample_pix[x,y] = (255,0,0,255)

		path = './current_experiment/sampling_rad/average/'
		sample_img.save( path + 'sig_' + str(sig).zfill(2) + '.png' )

	os._exit(1)

#=======================================================================[ Main ]

def main():

	# help?
	if 'h' in sys.argv or '-h' in sys.argv or '--h' in sys.argv or \
       'help' in sys.argv or '-help' in sys.argv or '--help' in sys.argv :
			printHelp()
			sys.exit()

	# create map only?
	if 'map' in sys.argv:
		ctrl.setup = Setup('./current_experiment/exp_setup')
		ctrl.world = WORLD.World( ctrl.setup.world )
		createMap()
		sys.exit()

	# no. of parameters
	if len(sys.argv) < 4:
		print('Error! At least four parameters are required to run the program.')
		sys.exit()

	# get trained SFA network from .tsn file
	tsn_file = sys.argv[1]

	if sys.argv[1] == '-':
		for f in os.listdir( './current_experiment/' ): 
			if '.tsn' in f: tsn_file = f
	if tsn_file == '-':
		print('Error! No .tsn file was found in folder \'./current_experiment\'.')
		print('This file is generated by train.py after training a network.')
		sys.exit()

	try:
		print('Loading .tsn file \'%s\'.' % tsn_file)
		tsn_file = open( './current_experiment/'+tsn_file, 'rb' )
	except:
		print('Error opening SFA network file!')
		sys.exit()

	ctrl.cfg.sfa_network = pickle.load( tsn_file )

	# get simulation setup from file
	print('Loading current experimental setup.')
	try:
		ctrl.setup = Setup( './current_experiment/exp_setup' )
		ctrl.defines.window_width  = int(ctrl.setup.rat.fov[0])
		ctrl.defines.window_height = int(ctrl.setup.rat.fov[1])
	except:
		print('Error! Could not find file \'./current_experiment/exp_setup\'.')
		print('(This file should is automatically generated by ratlab.py calls)')
		sys.exit()

	# check mode and set up opengl accordingly
	mode = 'spatial' if not 'dir' in sys.argv else 'directional'
	
	if mode == 'spatial':
		setupOpenGL( spatial=True )		# sets display_sampler_spatial as display loop function 

	elif mode == 'directional':
		setupOpenGL( spatial=False )	# sets display_sampler_directional as display loop function 

	# replicate original world setup
	ctrl.world = WORLD.World( ctrl.setup.world )

	# spatial sampling parameters
	if mode == 'spatial':
		try:
			ctrl.cfg.sample_period = int(sys.argv[2])
			ctrl.cfg.sample_order  = int(sys.argv[3])
		except:
			print('Error! The second and third parameters need to be integer values in order to')
			print('denote sampling period and sampling order respectively. Use \'-h\'for details.')
			sys.exit()
		for i, arg in enumerate(sys.argv):
			if   arg == 'prefix': ctrl.cfg.file_prefix = sys.argv[i+1]
			elif arg == 'setup':  ctrl.cfg.setup_file  = sys.argv[i+1]
			elif arg == 'v':      ctrl.cfg.verbose = True

		ctrl.cfg.verbose = True # mebbe this should be the default? (use <nv> to set non-verbose?)

	# directional sampling parameters
	elif mode == 'directional':
		try:
			ctrl.cfg.sample_order = int(sys.argv[2])
		except:
			print('Error! Second parameter does not denote sampling order.')
			sys.exit()

	# check / setup directories
	if mode == 'spatial':
		fail = False

		for folder in ['sampling_plots', 'sampling_values', 'sampling_values_raw']:

			if( os.path.isdir('./current_experiment/'+folder) == False ):
				try:	os.mkdir('./current_experiment/'+folder)
				except:	fail = True

			if( os.path.isdir('./current_experiment/'+folder+'/local') == False ):
				try:	os.mkdir('./current_experiment/'+folder+'/local')
				except:	fail = True

			if( os.path.isdir('./current_experiment/'+folder+'/average') == False ):
				try:	os.mkdir('./current_experiment/'+folder+'/average')
				except:	fail = True

		if fail:
			print('Error! Required folders could not be created.')
			sys.exit()

	elif mode == 'directional':
		fail = False

		if( os.path.isdir('./current_experiment/sampling_rad') == False ):
			try:    os.mkdir('./current_experiment/sampling_rad')
			except: fail = True

		if( os.path.isdir('./current_experiment/sampling_rad/local') == False ):
			try:    os.mkdir('./current_experiment/sampling_rad/local')
			except: fail = True

		if( os.path.isdir('./current_experiment/sampling_rad/average') == False ):
			try:    os.mkdir('./current_experiment/sampling_rad/average')
			except: fail = True

	# run sampler
	if mode == 'spatial':
		sample_spatial( sys.argv )      # parameters contain list of directions

	elif mode == 'directional':
		sample_directional( sys.argv )  # parameters contain grid setup

#-----------------------------------------------------------------------[ Help ]

def printHelp():
	print('================================================================================')
	print('RatLab sample help                                                              ')
	print('--------------------------------------------------------------------------------')
	print('This program uses a pre-trained SFA network hierarchy to sample a pre-defined')
	print('virtual environment by iterating a camera through the world and feeding its')
	print('visual input into the SFA network. The generated answers are collected, scaled')
	print('and stored to disk. (Note: the examples below assume train.py has been used to')
	print('train a network and store it to the file \'network_x5000_greyscale.tsn\'.)\n')
	print('There are two principal modes an environment can be sampled: Spatial and')
	print('directional.\n')
	print('Spatial sampling - The response of the network is plotted depending on location.')
	print('Thus, a sample plot shows the activity of one signal over the whole enclosure.')
	print('The aim of such a plot is to display direction invariance, i.e., the activity')
	print('of any signal over space does only depend on the location whithin that space and')
	print('not the direction the camera is looking at. In other words, a place field plot.\n')
	print('Directional samping - The response of the network is plotted depending on')
	print('direction and averaged over position. The aim of such a plot is to show location')
	print('invariance, i.e., the activity of a signal does only depend on the direction the')
	print('camera is looking at and not the actual location in space. In other words, a')
	print('head direction plot.\n')
	print('------------------------------------------------------[ Command Line Parameter ]\n')
	print('<tsn file>  The first parameter always has to name a .tsn (Trained Sfa Network)')
	print('            file from which a pre-trained SFA hierarchy network is read.')
	print('            NOTE: This parameter can be replaced by a simple \'-\', in which case')
	print('            the sampler simply uses the first .tsn file to be found in the')
	print('            \'./current_experiment\' folder.\n')
	print('map         If the parameter list inlcudes this option, no sampling takes place.')
	print('            Instead, an overview of the valid positions within the environment')
	print('            is being drawn, which essentially means a top down map of the')
	print('            enclosure. It can be used to verify the experimental setup and to')
	print('            manually set sampling points for directional sampling (see below).')
	print('v           If the v (for verbose) parameter is set, all spatial plots contain')
	print('            their maximum and minimum values in their respective file names.\n')
	print('------------------------------------------------------[ Spatial Plot Parameter ]\n')
	print('<period>    The second parameter sets the sampling period/frequency. A value of')
	print('            1 means that every (integer) position is being sampled, while a')
	print('            value of two would mean that only every second position within the')
	print('            environment is sampled (thus yielding a plot of half the dimensions')
	print('            as in the first case).\n')
	print('<signals>   The third parameter tells the program to deliver the response of the')
	print('            n slowest signals (normally, this should not be larger than 32).\n')
	print('<dir>       To specify the direction the camera should point to during sampling,')
	print('            a list of direction indicators is expected. These follow the compass')
	print('            rose and can be any of the following: \'n\', \'ne\', \'e\', \'se\', \'s\',')
	print('            \'sw\', \'w\', \'nw\' (denoting \'north\', \'north-east\', \'east\', and so on).')
	print('            it is also possible to simply use \'all\', which samples all eight')
	print('            directions consecutively.\n')
	print('--------------------------------------------------[ Directional Plot Parameter ]\n')
	print('<signals>   The second parameter tells the program to deliver the response of')
	print('            the n slowest signals (normally, this should not be larger than 32).\n')
	print('dir         For directional sampling, this parameter has to be set after naming')
	print('            a .tsn file and setting the <signals> parameter. It indicates that')
	print('            directional sampling is to be used.\n')
	print('grid <s>    This optional optional parameter specifies a regular grid of spacing')
	print('            <s> (i.e., a value of 20 denotes a grid with intersections at every')
	print('            20th position). Directional sampling then takes place at all the')
	print('            points specified by the grid. For example, a value of 1 would mean')
	print('            that every single position in the environment is sampled for the')
	print('            network activity in all (360) directions.\n')
	print('Since sampling by a grid parameter is a very thorough process, it takes a lot of')
	print('time and is very redundand. What can be done instead, is to run the sample')
	print('program with the optional <map> parameter, which creates an overview of the')
	print('environment and stores it in a file labeled \'exp_map.png\'. This map can be')
	print('opened and then used to mark individual positions with a single red pixel.')
	print('When subsequently calling the sample program with the <dir> parameter (to ')
	print('indicate directional sampling) and leaving out the <grid> parameter, the sample')
	print('program will look for the \'exp_map.png\' file and perform directional sampling')
	print('only at the indicated positions. This can be used to only sample at specific')
	print('locations of the environment to check for position invariance of firing.\n')
	print('--------------------------------------------------------------------[ Examples ]\n')
	print('While looking north, sample every (valid) position within the world and store')
	print('the activity of the five slowest signals to file:')
	print('     $ python sample.py network_x5000_greyscale.tsn 1 5 n\n')
	print('Sample every 10th step while looking north and south. Store the slowest response')
	print('only. In addition, use the only available .tsn file:')
	print('     $ python sample.py - 10 1 n s\n')
	print('Sample all 32 slowest signals over every position and direction; mark files with')
	print('prefix \'everything_\':')
	print('     $ python sample.py network_x5000_greyscale.tsn 1 32 all prefix everything_\n')
	print('Create a map of the environment (stored in file \'exp_map.png\'):')
	print('     $ python sample.py map\n')
	print('Create head direction plots for the 32 slowest signals. Sample head direction')
	print('over every single position:')
	print('     $ python sample.py network_x5000_greyscale.tsn 32 grid 1 dir\n')
	print('Create head direction plots as above, but sample only at two distinct positions')
	print('drawn into the file \'exp_map.png\' which was created earlier:')
	print('     $ python sample.py network_x5000_greyscale.tsn 32 dir\n')
	print('================================================================================')

main() # <<<   <<<   <<<   <<<   <<<   <<<   <<<   <<<   <<<   <<<   <<<[ main ]

