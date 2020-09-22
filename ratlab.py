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
import pickle

# math
import math
import numpy

# python image library
from PIL import Image as img

# OpenGL
from OpenGL.GLUT import *
from OpenGL.GLU  import *
from OpenGL.GL   import *

# utilities / own
sys.path.append( './util' )
from util.setup import *
import world
import ratbot
import opengl_text as text


#--------------------------------------------------------------------[ control ]

class LocalControl( Freezeable ):
	def __init__( self ):

		# define: set for the current version
		self.defines = EmptyOptionContainer()	# defines
		self.defines.window_title  = 'RatLab v2.4'
		self.defines.window_width  =  800
		self.defines.window_height =  600
		self.defines.aspect_ratio  =  800.0/600.0
		self.defines.freeze()

		# config: no change during runtime
		self.config = EmptyOptionContainer()	# config
		self.config.record        = False
		self.config.limit         = None
		self.config.run_wallcheck = False
		self.config.freeze()

		# option: may change during runtime
		self.options = EmptyOptionContainer()	# options
		self.options.show_overview  = True
		self.options.show_ratview   = True
		self.options.show_progress  = False
		self.options.sketch_uniform = False
		self.options.ratview_scale  = 1
		self.options.freeze()

		# module: separate part of the program
		self.modules = EmptyOptionContainer()	# modules
		self.modules.world    = None
		self.modules.rat      = None
		self.modules.datafile = None
		self.modules.freeze()
		
		# state: set and used only by the program
		self.state = EmptyOptionContainer() 	# state
		self.state.step           = 0
		self.state.last_view      = None
		self.state.shot_count     = 0
		self.state.starting_time  = None
		self.state.freeze()
		
		self.setup = Setup()					# global control
		self.freeze()

ctrl = LocalControl()


#===================================================================[ callback ]

def __keyboardPress__( key, x, y ):
	# c: switch uniform sketch
	if str(key, 'utf-8') == 'c':  # Convert bytes object to string
		ctrl.options.sketch_uniform = not ctrl.options.sketch_uniform

	# ESC: quit program
	elif ord(key) == 27:
		print('- User abort -')
		if ctrl.config.record: 
			ctrl.modules.datafile.close()	
		os._exit(1)

def __keyboardSpecialPress__( key, x, y ):

	# F1: show/hide map overview
	if key == GLUT_KEY_F1:
		ctrl.options.show_overview = not ctrl.options.show_overview

	# F2: show/hide ratview
	elif key == GLUT_KEY_F2 and ctrl.config.record == False:
		ctrl.options.show_ratview = not ctrl.options.show_ratview

	# F3: show/hide progress bar
	elif key == GLUT_KEY_F3 and ctrl.config.limit != None:
		ctrl.options.show_progress = not ctrl.options.show_progress

	# F4: switch ratview size
	elif key == GLUT_KEY_F4:
		if ctrl.options.ratview_scale == 1:
			ctrl.options.ratview_scale = 2
		else:
			ctrl.options.ratview_scale = 1

	# F12: take screenshot
	elif key == GLUT_KEY_F12:
		ctrl.state.shot_count += 1
		filename = './current_experiment/screenshot_' + str(ctrl.state.shot_count).zfill(3) + '.png'
		screenshot = glReadPixels( 0,0, ctrl.defines.window_width, ctrl.defines.window_height, GL_RGBA, GL_UNSIGNED_BYTE )
		im = img.frombuffer('RGBA', (ctrl.defines.window_width,ctrl.defines.window_height), screenshot, 'raw', 'RGBA', 0, 0 )
		im.save( filename )
		print('  Screenshot saved to file \'%s\'.' % (filename))


#===============================================================[ OpenGL Setup ]

def __setupGlut__():
	# create GLUT window
	glutInit( sys.argv )
	glutInitDisplayMode( GLUT_DOUBLE |
                         GLUT_RGBA   |
                         GLUT_DEPTH  )
	glutInitWindowSize( ctrl.defines.window_width, ctrl.defines.window_height )
	glutCreateWindow(b'Ratlab v2.4' )

	# display
	glutDisplayFunc( __display__ )
	glutTimerFunc( 0, __drawcall__, 1 )

	# callback
	glutKeyboardFunc( __keyboardPress__ )
	glutSpecialFunc( __keyboardSpecialPress__ )

	# set cursor
	glutSetCursor( GLUT_CURSOR_CROSSHAIR )

	#glutSetOption(GLUT_ACTION_ON_WINDOW_CLOSE, GLUT_ACTION_CONTINUE_EXECUTION);
    
def __setupOpenGL__():
	# projection matrix setup w/ default viewport
	# glViewport( 0, 0, ctrl.defines.window_width, ctrl.defines.window_height )

	glMatrixMode( GL_PROJECTION )
	glLoadIdentity()
	gluPerspective( ctrl.setup.rat.fov[1],
		            ctrl.defines.aspect_ratio,
		            ctrl.setup.opengl.clip_near,
		            ctrl.setup.opengl.clip_far )

	# viewing matrix setup
	glMatrixMode( GL_MODELVIEW )
	glLoadIdentity()

	# misellaneous parameters
	clear_color = ctrl.setup.world.color_background
	glClearColor( clear_color[0], clear_color[1], clear_color[2], 0.0 )
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


#====================================================================[ Drawing ]

def __drawcall__( i ):
	glutPostRedisplay()
	glutTimerFunc( 0, __drawcall__, 1 )

def __display__():
    
	# main reset
	glClear( GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT )
	glBindTexture( GL_TEXTURE_2D, 0 )

	# get rat's next state
	rat_state = ctrl.modules.rat.nextPathStep()

	#-----------------------------------------------[ map overview / wallcheck ]

	if ctrl.options.show_overview == True or ctrl.config.run_wallcheck == True:
		# opengl
		glViewport( 40, 150, 720, 450 )
		glMatrixMode( GL_PROJECTION )
		glLoadIdentity()
		gluPerspective( 40.0, 720.0/450.0, 2.0, 512.0 ) # fov, ratio, near, far
		glMatrixMode( GL_MODELVIEW )
		glLoadIdentity()
		# camera
		limits = ctrl.setup.world.limits
		gluLookAt( (limits[0]+limits[2])/2.0, -limits[3], 300,
				   (limits[0]+limits[2])/2.0,  (limits[1]+limits[3])/2.0, 0,
				   0.0, 0.0, 1.0 )
		# default overview render
		if ctrl.config.run_wallcheck == False:
			ctrl.modules.world.sketchWorld( sketch_uniform = ctrl.options.sketch_uniform )
			ctrl.modules.world.sketchPath ( ctrl.modules.rat.getPath() )
			ctrl.modules.world.sketchArrow( rat_state[0][0], rat_state[0][1], rat_state[1][0], rat_state[1][1] )
		# wallcheck render
		else:
			for i, raster in enumerate([False,True]):
				ctrl.modules.world.sketchWorld( sketch_info = True, raster=raster )
				# read frame buffer into image
				screenshot = glReadPixels( 0,0, ctrl.defines.window_width, ctrl.defines.window_height, GL_RGBA, GL_UNSIGNED_BYTE )
				im = img.frombuffer('RGBA', (ctrl.defines.window_width,ctrl.defines.window_height), screenshot, 'raw', 'RGBA', 0, 0 )
				im.save( './current_experiment/wallcheck_'+('raster' if raster==True else '')+'.png' )
			# exit
			print('Wallcheck screenshots saved to working directory \'./current_experiment\'.')
			os._exit(1)
	
	#-----------------------------------------------------------[ progress bar ]

	if ctrl.options.show_progress:
		glViewport( 0, 0, 800, 600 )
		glMatrixMode( GL_PROJECTION )
		glLoadIdentity()
		gluOrtho2D( -300, 300, -300, 300 )
		glMatrixMode( GL_MODELVIEW )
		glLoadIdentity()
		text.drawProgressBar( ctrl.config.limit, ctrl.state.step+1, (-130,-250) )
		
	#-----------------------------------------------------[ rat view rendering ]

	if ctrl.options.show_ratview == True:

		glColor( 1.0, 1.0, 1.0 )

		dir_n  = numpy.array( [rat_state[1][0],rat_state[1][1]] )
		dir_n /= math.sqrt( dir_n[0]**2 + dir_n[1]**2 )
		dir_a  = math.asin( abs(dir_n[1]) ) * ctrl.setup.constants.RAD2DEG

		if   dir_n[0]<=0 and dir_n[1]>=0: dir_a =180.0-dir_a
		elif dir_n[0]<=0 and dir_n[1]<=0: dir_a =180.0+dir_a
		elif dir_n[0]>=0 and dir_n[1]<=0: dir_a =360.0-dir_a

		x = int( ctrl.defines.window_width/2 - ctrl.setup.rat.fov[0]/2*ctrl.options.ratview_scale )
		for i in range( int(dir_a-ctrl.setup.rat.fov[0]/2), int(dir_a+ctrl.setup.rat.fov[0]/2)+1 ):

			glViewport( x, 80, 1*ctrl.options.ratview_scale, int(ctrl.setup.rat.fov[1])*ctrl.options.ratview_scale )
		
			glMatrixMode( GL_PROJECTION )
			glLoadIdentity()
			gluPerspective( ctrl.setup.rat.fov[1], 1.0/ctrl.setup.rat.fov[1], 
							ctrl.setup.opengl.clip_near, ctrl.setup.opengl.clip_far )

			glMatrixMode( GL_MODELVIEW )
			glLoadIdentity()

			focus = [ rat_state[0][0]+math.cos(i*ctrl.setup.constants.DEG2RAD)*100.0,
					  rat_state[0][1]+math.sin(i*ctrl.setup.constants.DEG2RAD)*100.0,
					  ctrl.setup.world.cam_height ]

			gluLookAt( rat_state[0][0], rat_state[0][1], ctrl.setup.world.cam_height,
				       focus[0], focus[1], focus[2], 
				       0,0,1 )

			ctrl.modules.world.drawWorld( focus )
			x+=ctrl.options.ratview_scale
            
	#---------------------------------------------------[ simulation recording ]

	# read out current rat view image
	opengl_buffer = glReadPixels( ctrl.defines.window_width/2 - ctrl.setup.rat.fov[0]/2*ctrl.options.ratview_scale,
		                          80, ctrl.setup.rat.fov[0], ctrl.setup.rat.fov[1], GL_RGBA, GL_UNSIGNED_BYTE )

	ctrl.state.last_view  = img.frombuffer( 'RGBA', (int(ctrl.setup.rat.fov[0]),int(ctrl.setup.rat.fov[1])), 
											 opengl_buffer, 'raw', 'RGBA', 0, 0 )

	# recording
	if ctrl.config.record == True:

		# save current rat view to the image sequence
		if ctrl.setup.rat.color == 'RGB':
			ctrl.state.last_view.save( './current_experiment/sequence/frame_'+str(ctrl.state.step).zfill(5)+'.png' )
		elif ctrl.setup.rat.color == 'greyscale':
			last_view_grayscale = ctrl.state.last_view.convert( 'L' )
			last_view_grayscale.save( './current_experiment/sequence/frame_'+str(ctrl.state.step).zfill(5)+'.png' )
		elif ctrl.setup.rat.color == 'duplex':
			ctrl.state.last_view.save( './current_experiment/sequence_color/frame_'+str(ctrl.state.step).zfill(5)+'.png' )
			last_view_grayscale = ctrl.state.last_view.convert( 'L' )
			last_view_grayscale.save( './current_experiment/sequence/frame_'+str(ctrl.state.step).zfill(5)+'.png' )

		# collect movement data
		ctrl.modules.datafile.write(str(ctrl.state.step) + ' ' +
									str(rat_state[0][0]) + ' ' + str(rat_state[0][1]) + ' ' +
									str(rat_state[1][0]) + ' ' + str(rat_state[1][1]) + '\n')

	# simulation step counter
	ctrl.state.step += 1

	# runtime limit
	if ctrl.config.limit != None:

		# print progress
		sys.stdout.write( '\rStep ' + str(ctrl.state.step) + '/' + str(ctrl.config.limit) )
		sys.stdout.flush()

		# save a screenshot of the final frame 
		if ctrl.state.step == ctrl.config.limit:

			screenshot = glReadPixels( 0,0, ctrl.defines.window_width, ctrl.defines.window_height, GL_RGBA, GL_UNSIGNED_BYTE)
			im = img.frombuffer('RGBA', (ctrl.defines.window_width,ctrl.defines.window_height), screenshot, 'raw', 'RGBA', 0, 0)
			im.save('./current_experiment/exp_finish.png')

			print(' - all done.\nExperimental data saved to folder \'./current_experiment\':')
			print('   Final simulation state:  \'exp_finish.png\'.')
			print('   Experiment parameters:   \'exp_setup\'.')
			print('   Image sequence:          \'/sequence\'')
			if ctrl.setup.rat.color == 'duplex':
				print('   Duplex color sequence:   \'/sequence_color\'.')
			if ctrl.config.record: 
				ctrl.modules.datafile.close()
				print('   Rat trajectory:          \'exp_trajectory.txt\'.')

			print('Runtime: %dsec / %dmin' % (time.time()-ctrl.state.starting_time, (time.time()-ctrl.state.starting_time)/60.0))

			os._exit(1)

		# force overview in order to have it shown when the final frame is saved as a screenshot
		if ctrl.state.step+1 == ctrl.config.limit:
			ctrl.options.show_overview = True

	#------------------------------------------------------------[ end drawing ]

	glutSwapBuffers()


#=======================================================================[ Main ]

def main():
	
	# help?
	if '-h' in sys.argv or 'h' in sys.argv or '--help' in sys.argv or 'help' in sys.argv:
		printHelp()
		os._exit(1)

	# create required folders if necessary
	if( os.path.isdir('./current_experiment') == False ):
		try:    os.mkdir('./current_experiment')
		except: return

	if( os.path.isdir('./current_experiment/sequence') == False ):
		try:	os.mkdir('./current_experiment/sequence')
		except: return

	if 'duplex' in sys.argv:
		if( os.path.isdir('./current_experiment/sequence_color') == False ):
			try:	os.mkdir('./current_experiment/sequence_color')
			except: return

	# command line arguments
	for i, arg in enumerate( sys.argv ):

		# recording
		if arg == 'record':  
			ctrl.config.record = True
			ctrl.modules.datafile = open( './current_experiment/exp_trajectory.txt', 'w' )
		elif arg == 'limit':   
			ctrl.config.limit = int( sys.argv[i+1] )
			ctrl.options.show_overview = False
			ctrl.options.show_ratview  = True
			ctrl.options.show_progress = True

		# world setup parameters
		elif arg == 'no_wallmix': ctrl.setup.world.wallmix  = False
		elif arg == 'boxmix':     ctrl.setup.world.boxmix   = True
		elif arg == 'box':        ctrl.setup.world.obstacles.append( [float(sys.argv[i+1]),float(sys.argv[i+2]),float(sys.argv[i+3]),float(sys.argv[i+4])] )
		elif arg == 'dbox':       ctrl.setup.world.obstacles.append( [float(sys.argv[i+1]),float(sys.argv[i+2]),float(sys.argv[i+1])+ctrl.setup.world.box_dim[0],float(sys.argv[i+2])+ctrl.setup.world.box_dim[1]] )
		elif arg == 'dim':
			ctrl.setup.world.dim[0] = sys.argv[i+1]  # length
			ctrl.setup.world.dim[1] = sys.argv[i+2]  # width
			ctrl.setup.world.dim[2] = sys.argv[i+3]  # height
		elif arg == 'star_maze' or arg == 'S':
			ctrl.setup.world.type = 'star'
			ctrl.setup.world.dim = numpy.zeros([4], dtype=numpy.int32)
			ctrl.setup.world.dim[0] = sys.argv[i+1]  # no. of arms
			ctrl.setup.world.dim[1] = sys.argv[i+2]  # width of an arm
			ctrl.setup.world.dim[2] = sys.argv[i+3]  # length of an arm
			ctrl.setup.world.dim[3] = sys.argv[i+4]  # wall height of an arm
		elif arg == 't_maze' or arg == 'T':
			ctrl.setup.world.type = 'T'
			ctrl.setup.world.dim = numpy.zeros([5], dtype=numpy.int32)
			ctrl.setup.world.dim[0] = sys.argv[i+1]  # vertical arm length
			ctrl.setup.world.dim[1] = sys.argv[i+2]  # vertical arm width
			ctrl.setup.world.dim[2] = sys.argv[i+3]  # horizontal arm length
			ctrl.setup.world.dim[3] = sys.argv[i+4]  # horizontal arm width
			ctrl.setup.world.dim[4] = sys.argv[i+5]  # general arm height
		elif arg == 'circle_maze' or arg == 'o':
			ctrl.setup.world.type = 'circle'
			ctrl.setup.world.dim = numpy.zeros([3], dtype=numpy.int32)
			ctrl.setup.world.dim[0] = sys.argv[i+1]  # radius
			ctrl.setup.world.dim[1] = sys.argv[i+2]  # no. of wall segments
			ctrl.setup.world.dim[2] = sys.argv[i+3]  # general wall height
		elif arg == 'custom_maze' or arg == 'C':
			if 'box' in sys.argv or 'dbox' in sys.argv:
				print('Error! Boxes have to be specified by hand when using a custom maze (i.e., in the')
				print('custom maze description file).')
				os._exit(1);
			ctrl.setup.world.type = 'file'
			ctrl.setup.world.dim  = sys.argv[i+1]    # file name
		elif arg == 'wallcheck': 
			ctrl.config.run_wallcheck = True
		elif arg == 'path':
			ctrl.setup.rat.path = sys.argv[i+1]

		# experiment configuration parameters
		elif arg == 'grey':      ctrl.setup.rat.color     = 'greyscale'
		elif arg == 'duplex':    ctrl.setup.rat.color     = 'duplex'
		elif arg == 'small_fov': ctrl.setup.rat.fov       = numpy.array([55.0,35.0])
		elif arg == 'arc':       ctrl.setup.rat.arc       = int  ( sys.argv[i+1] )
		elif arg == 'dev':       ctrl.setup.rat.path_dev  = float( sys.argv[i+1] )
		elif arg == 'mom':       ctrl.setup.rat.path_mom  = float( sys.argv[i+1] )
		elif arg == 'speed':     ctrl.setup.rat.speed     = float( sys.argv[i+1] )
		elif arg == 'loop':      ctrl.setup.rat.path_loop = True
		elif arg == 'bias':
			ctrl.setup.rat.bias   = numpy.array( [float(sys.argv[i+1]),float(sys.argv[i+2])] )
			ctrl.setup.rat.bias  /= math.sqrt( ctrl.setup.rat.bias[0]**2 + ctrl.setup.rat.bias[1]**2 )
			ctrl.setup.rat.bias_s = float(sys.argv[i+3])

	# store setup parameters for later reconstruction
	if ctrl.setup.rat.color != 'duplex':
		ctrl.setup.toFile('./current_experiment/exp_setup')
	else:
		ctrl.setup.rat.color = 'greyscale'
		ctrl.setup.toFile('./current_experiment/exp_setup')
		ctrl.setup.rat.color = 'color'
		ctrl.setup.toFile('./current_experiment/exp_setup_color')
		ctrl.setup.rat.color = 'duplex'

	# welcome message
	print('Welcome to RatLab (v3.1)')
	print('Use command line option \'-h\', \'h\', \'help\' or \'--help\' to display available\ncommand line parameters\n')

	# set up core OpenGL modules
	__setupGlut__()
	__setupOpenGL__()
	  
	# create new world object
	ctrl.modules.world = world.World( ctrl.setup.world )

	# place rat at random initial position (rat chooses path[0] if path is given)
	ctrl.modules.rat = ratbot.RatBot( ctrl.modules.world.randomPosition(), ctrl )

	# start main loop
	ctrl.state.starting_time = time.time()
	glutMainLoop()
   
#-----------------------------------------------------------------------[ help ]

def printHelp():
	print('========================================================================[ v2.2 ]')
	print('RatLab help                                                                     ')
	print('--------------------------------------------------------------------------------')
	print('This program allows the setup of a virtual rat maze experiment. The environment')
	print('as well as the behavior of the rat may be fully specified according to the')
	print('available parameters below. In order to further use the generated data, the most')
	print('import option allows the recording of the simulated rat\'s vision during the')
	print('experiment in a series of .png images.')
	print('When finished, a folder \'./current_experiment\' is created, which contains all')
	print('created data so far:\n')
	print('- A subfolder \'/sequence\' which stores a recorded image sequence')
	print('- A screenshot titled \'exp_finish.png\', depicting the final state of the')
	print('  experiment (i.e., the complete path as run by the simulated rat).')
	print('- A file titled \'exp_setup\', which holds all the parameters defining the')
	print('  experiment (like the locations of optional obstacles or any rat behavior')
	print('  modifications such as a directional bias).')
	print('- An optional folder called \'sequence_color\', in case the experiment was')
	print('  recorded both in a color image sequence as well as a greyscale one.')
	print('- An optional file titled \'exp_trajectory.txt\', storing the exact sequence of')
	print('  locations visited by the simulated rat over the course of the experiment\n')
	print('Note that ratlab.py provides merely the initial data producing experiment. To')
	print('further evaluate the generated data, the convert.py program is used to create a')
	print('single datafile from the original image sequence. This file is then used by')
	print('the train.py program to train a SFA hierarchy on the data set. Finally, the')
	print('trained network is then used by the sample.py program in order to sample the')
	print('network\'s activity over the whole original environment as it was specified in')
	print('the original call to ratlab.py. The working directory for all programs is the')
	print('\'./current_experiment\' folder: they all assume it to exist and will use it to')
	print('store their respective output files in.\n')
	print('-----------------------------------------------------------------[ Mapped Keys ]\n')
	print('ESC - Quit the program.')
	print('F1  - Toggle Map Overview.')
	print('F2  - Toggle virtual rat view.')
	print('F3  - Toggle progress bar (only if a limit is set).')
	print('F4  - Switch between available rat view scales (x1 or x2).')
	print('F12 - Save a screenshot under the name \'./screenshot_<number>.png\' in the')
	print('      working directory \'./current_experiment\'.\n')
	print('-----------------------------------[ Command Line Options :: Experimental Setup ]\n')
	print('limit <x>   Automatically quits the simulation after <x> steps. When used, the')
	print('            default world map is switched off to facilitate easy timing runs.')
	print('            Once finished, a screenshot of the final state of the simulation is')
	print('            stored as \'final.png\'\n')
	print('record      Save a screenshot during every frame. The numbered image files are')
	print('            stored in the ./sequence folder.')
	print('            [Default: False]\n')
	print('grey        By default, recorded image sequences are stored in color/RGB format.')
	print('            Setting this flag will result in greyscale sequences instead.\n')
	print('duplex      Setting this flag will lead to two separate images being stored for')
	print('            every frame when recording: one greyscale, and one RGB color.\n')
	print('------------------------------------------[ Command Line Options :: Environment ]\n')
	print('dim <dim_x> <dim_y> <dim_z>')
	print('            The default experimental setup is a simple rectangular box. This')
	print('            parameter can be used to specify the dimensions of this box, where')
	print('            the dimensions x,y,z denote length, width, and height respectively')
	print('            [Default: 300 x 200 x 100]\n')
	print('star_maze <arms> <arm_width> <arm_length> <arm_height>')
	print('            This parameter sets up a star maze experiment. The environment in')
	print('            this case is built from <arms> corridors leading away from a common')
	print('            center. The width of each arm of the maze if given by <arm_width>,')
	print('            its length by <arm_length and its height by <arm_height>. Note that')
	print('            the sortcut \'S\' can be used instead of the \'star_maze\' parameter.\n')
	print('t_maze <vrt_length> <vrt_width> <hrz_length> <hrz_width> <wall_height>')
	print('            This parameter sets up a T-maze experiment. The environment will in')
	print('            this case consist of a vertical corridor of length <vrt_length> and')
	print('            width <vrt_width>, and a horizontal corridor of length <hrz_length')
	print('            and of width <hrz_width>. All walls of the maze have the uniform')
	print('            height of <wall_height>. Note that the shortcut \'T\' can be used')
	print('            instead of the full \'t-maze\' parameter.\n')
	print('circle_maze <radius> <segments> <height>')
	print('            This paremeter sets up a circular environment. The enclosed area')
	print('            will have a radius of <radius> and a uniform wall height of <height>.')
	print('            Note that the shortcut \'o\' can be used instead of \'circle_maze\'.\n')
	print('custom_maze <file_name>')
	print('            This parameter allows the setup of an environment fully specified by')
	print('            the user. The parameter <file_name> has to denote a file lying in the')
	print('            ./current_experiment/ folder. Each line in this file needs to specify')
	print('            a single wall segment, and needs to be formated like the following:')
	print('              \"from_x   from_y   to_x   to_y   texture_name\"')
	print('            where the first two parameters denote the XY coordinates of the')
	print('            wall\'s starting point, and the following parameters the coordinates')
	print('            of its end point. <texture_name> needs to be the name of a file')
	print('            located in the \'./textures\' folder (without the file ending).')
	print('            NOTE: Walls merely have a front side and NO back side! This means')
	print('            that the points <from> and <to> need to correspond wall\'s left and')
	print('            right end respectively.')
	print('            NOTE: You might also want to manually set the floor texture by adding')
	print('            an optional line \"floor <name>\", where the paramater <name> follows')
	print('            the same rule as the texture parameter for a wall segmant as')
	print('            described above.')
	print('            NOTE: To check a valid setup use \'wallcheck\' as an additional')
	print('            parameter (see below for details).')
	print('            NOTE: An example world file can be found in the \'./tools\' folder')
	print('            under the name \'custom_example_world.txt\'.')
	print('            NOTE: the \'box\' and \'dbox\' parameters do NOT work in custom')
	print('            environments; boxes have to be specified manually in the file.\n')
	print('wallcheck   This parameter lets ratlab render an overview of the environment')
	print('            as set up by the given parameters. This overview contains additional')
	print('            information, such as the vertices of wall segments and their normal')
	print('            vectors. Use this parameter in conjunction with the \'custom_maze\'')
	print('            parameter to check for wrongly flipped walls and seamless connection')
	print('            of all the wall segments. Specifically, all normal vectors should')
	print('            point INWARDS for the walls to actually close off the environment. If')
	print('            a wall\'s normal vector, and thus it\'s front side points in the')
	print('            wrong direction, simply switch it\'s specified from/to coordinates in')
	print('            the respective file.')
	print('no_wallmix  By default, each wall of the environment has a different texture ')
	print('            (color as well as pattern). Using this paramater forces each wall to')
	print('            display the same texture.\n')
	print('boxmix      Apply different textures to the world\'s obstacles.')
	print('            [Default: False]\n')
	print('box <ll_x> <ll_y> <ur_x> <ur_y>')
	print('            Add a rectangular obstacle to the world, defined by its lower left')
	print('            corner ( <ll_x>, <ll_y> ) and upper right corner ( <urx>, <ury> ).\n')
	print('dbox <ll_x> <ll_y>')
	print('            Add a default-sized box to the world, which only requires the lower')
	print('            left corner coordinates ( <ll_x>, <ll_y> ).\n')
	print('-----------------------------------------[ Command Line Options :: Rat Behavior ]\n')
	print('small_fov   Sets an alternative field of view of 55x35 degrees.\n')
	print('speed <s>   Speed multiplier for the virtual rat\'s movement.')
	print('            [Default: 1.0]\n')
	print('arc <x>     Sets the virtual rat\'s decision arc. A value of 360 (degrees)')
	print('            corresponds to completely random path behaviour, while a value of 5')
	print('            leads to the rat running in more or less straight lines.')
	print('            [Default: 320]\n')
	print('mom <x>     Sets the momentum term of the rat\'s movement. Has to lie between 0')
	print('            and 1, and effectively describes the smoothness of the path.')
	print('            [Default: 0.8]\n')
	print('path <file_name>')
	print('            The rat follows a series of waypoints given by the file <file_name>')
	print('            residing in the \'./current_experiment\' directory. In the \'./tools\'\n')
	print('            directory you can find and look at an example file. Note that when')
	print('            using a custom path, the simulation does not check for valid')
	print('            positions along the path any more. Make sure that any specified path')
	print('            does not lead to the rat walking through any walls before committing')
	print('            to a full scale simulation.\n')
	print('loop        This parameter is only used when the rat follows a custom path given')
	print('            by the above parameter and file name. If loop is active, the rat')
	print('            will run back the first waypoint upon reaching the last one. If it')
	print('            is not set, the rat will be reset at the first waypoint upon')
	print('            reaching the last one')
	print('            [Default: False]')
	print('bias <dir_x> <dir_y> <s>')
	print('            Introduce a movement bias: When running in the direction specified')
	print('            by the vector ( <dir_x>, <dir_y> ) the virtual rat will move faster')
	print('            than in the orthogonal direction. The scaling factor <s> determines')
	print('            how much speed is added in the bias direction (a value of 1.0')
	print('            doubles the movement speed if the rat\'s velocity is perfectly')
	print('            aligned with the bias vector.')
	print('            Note: There is no default value for the scalar factor <s>. Thus')
	print('            when setting a bias, the scalar HAS to be set as well.')
	print('            [Default: (0,0); no bias direction]\n')
	print('--------------------------------------------------------------------[ Examples ]\n')
	print('Record 500 steps (greyscale images) and quit:')
	print('    $ python ratlab.py limit 500 record\n')
	print('Record 500 steps in greyscale AND color and quit:')
	print('    $ python ratlab.py limit 500 record duplex\n')
	print('Modified path behaviour in an obstructed world:')
	print('    $ python ratlab.py fov 100 arc 10 wallmix dbox 100 50 dbox 230 150\n')
	print('Move faster along north/south axis (Note that bias direction works both ways):')
	print('    $ python ratlab.py bias 0 1 1.0\n')
	print('Run the same experiment in an eight arm star maze:')
	print('    $ python ratlab.py bias 0 1 1.5 star_maze 8 40 80 100')
	print('================================================================================')

main() # <<<   <<<   <<<   <<<   <<<   <<<   <<<   <<<   <<<   <<<   <<<[ main ]

