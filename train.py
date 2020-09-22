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


#====================================================================[ Imports ]

# system
import os
import sys
import time
import struct
import pickle

# math
import numpy
import math
import mdp

print('Running MDP version', mdp.__version__)# , mdp.config.has_mdp, 'from', mdp.__file__

# utilities / own
sys.path.append( './util' )
from util.setup import *


#==================================================================[ Utilities ]

# grab data slice from fully loaded data set
class getReusableDataSlicer():
	def __init__( self, data, batch_size ):
		self.data = data
		self.batch_size = batch_size
	def __iter__( self ):
		for i in range( int(self.data.shape[0]/self.batch_size) ):
			yield self.data[ i*self.batch_size:(i+1)*self.batch_size, ]

def printNetworkState( network ):
	# color/greyscale, wide/narrow?
	print('\tNetwork (%d layers) accepts' % len(network), ('COLOR' if network[0].in_channel_dim==3 else 'GREYSCALE'))
	print('images with a', ('WIDE' if network[0].in_channels_xy[0]==320 else 'NARROW'), 'FOV angle.')
	# trained?
	print('\tLower SFA layer 01: ', ('NOT trained.' if network[1].is_training() else 'IS trained.'))
	print('\tLower SFA layer 02: ', ('NOT trained.' if network[3].is_training() else 'IS trained.'))
	print('\tHigh lvl SFA layer: ', ('NOT trained.' if network[4].is_training() else 'IS trained.'))
	if len(network)==6:
		print('\tHigh lvl ICA layer: ', ('NOT trained.' if network[5].is_training() else 'IS trained.'))
	else:
		print('\t(Network does not have an ICA layer)')


#=======================================================[ SFA Network Training ]

def initNetwork( wide_fov=True, color=True, noise=False ):

	# wide angle setup
	if wide_fov:
		raw_data_dim_x           =320
		raw_data_dim_y           = 40

		sfa_dim_red_factor       = 32	# output dimension of sfa nodes used for dimensionality reduction

		sfa_lower_layer_nodes_x  = 63	# 63x9=567 -> no. output channels of the raw switchboard
		sfa_lower_layer_nodes_y  =  9
		sfa_lower_layer_field_x  = 10	# 10x8x1=80 -> dimension of a single output channel of raw switchboard
		sfa_lower_layer_field_y  =  8
		sfa_lower_layer_node_out = 32	# output dimension of a single node of sfa clone layer A

		sfa_upper_layer_nodes_x  =  8	# 8x2=10 -> no. output channels of the sfa switchboard
		sfa_upper_layer_nodes_y  =  2
		sfa_upper_layer_field_x  = 14	# 14x6x16=1344 -> dimensions of a single output channel of the sfa switchboard
		sfa_upper_layer_field_y  =  6
		sfa_upper_layer_node_out = 32	# output dimension of a single node of sfa clone layer B

		sfa_top_node_out		 = 32	# output dimension of the single SFA node atop the hierarchy

	# narrow angle setup
	else:
		raw_data_dim_x           = 55
		raw_data_dim_y           = 35

		sfa_dim_red_factor       = 32	# output dimension of sfa nodes used for dimensionality reduction

		sfa_lower_layer_nodes_x  = 10
		sfa_lower_layer_nodes_y  =  6
		sfa_lower_layer_field_x  = 10
		sfa_lower_layer_field_y  = 10
		sfa_lower_layer_node_out = 32	# output dimension of a single node of sfa clone layer A

		sfa_upper_layer_nodes_x  =  4
		sfa_upper_layer_nodes_y  =  4
		sfa_upper_layer_field_x  =  4
		sfa_upper_layer_field_y  =  2
		sfa_upper_layer_node_out = 32	# output dimension of a single node of sfa clone layer B

		sfa_top_node_out		 = 32	# output dimension of the single SFA node atop the hierarchy

	#--------------------------------------------------------[ Lower SFA Layer ]

	# raw data switchboard
	raw_switchboard = mdp.hinet.Rectangular2dSwitchboard( in_channels_xy    = (raw_data_dim_x,raw_data_dim_y),
														  field_channels_xy = (sfa_lower_layer_field_x,sfa_lower_layer_field_y),
														  field_spacing_xy  = (sfa_lower_layer_field_x//2,sfa_lower_layer_field_y//2),
														  in_channel_dim    = 3 if color else 1 )
	# processing over-node for lower sfa layer
	sfa_node_A = mdp.nodes.SFANode               ( input_dim=raw_switchboard.out_channel_dim, output_dim=sfa_dim_red_factor, dtype='float32' )
	exp_node   = mdp.nodes.QuadraticExpansionNode( input_dim=sfa_dim_red_factor )
	noise_node = mdp.nodes.NoiseNode             ( input_dim=exp_node.output_dim, output_dim=exp_node.output_dim, noise_args=(0,numpy.sqrt(0.05)) )
	sfa_node_B = mdp.nodes.SFANode               ( input_dim=exp_node.output_dim, output_dim=sfa_lower_layer_node_out, dtype='float32' )

	if noise:
		sfa_over_node  = mdp.hinet.FlowNode( mdp.Flow([ sfa_node_A, exp_node, noise_node, sfa_node_B ]) )
		print('Using noisy nodes.')
	else:
		sfa_over_node  = mdp.hinet.FlowNode( mdp.Flow([ sfa_node_A, exp_node, sfa_node_B ]) )

	# lower clone layer
	sfa_lower_layer = mdp.hinet.CloneLayer( sfa_over_node, n_nodes=raw_switchboard.output_channels )

	#--------------------------------------------------------[ Upper SFA Layer ]
	
	# sfa data relay switchboard
	sfa_switchboard = mdp.hinet.Rectangular2dSwitchboard( in_channels_xy    = (sfa_lower_layer_nodes_x,sfa_lower_layer_nodes_y),
														  field_channels_xy = (sfa_upper_layer_field_x, sfa_upper_layer_field_y),
														  field_spacing_xy  = (sfa_upper_layer_field_x//2,sfa_upper_layer_field_y//2),
														  in_channel_dim    = sfa_lower_layer_node_out )
	# processing over-node for upper sfa layer 
	sfa_node_X = mdp.nodes.SFANode				 ( input_dim=sfa_switchboard.out_channel_dim, output_dim=sfa_dim_red_factor, dtype='float32' )
	exp_node   = mdp.nodes.QuadraticExpansionNode( input_dim=sfa_dim_red_factor )
	noise_node = mdp.nodes.NoiseNode             ( input_dim=exp_node.output_dim, output_dim=exp_node.output_dim, noise_args=(0,numpy.sqrt(0.05)) )
	sfa_node_Y = mdp.nodes.SFANode				 ( input_dim=exp_node.output_dim, output_dim=sfa_upper_layer_node_out, dtype='float32' )

	if noise:
		sfa_over_node  = mdp.hinet.FlowNode( mdp.Flow([ sfa_node_X, exp_node, noise_node, sfa_node_Y ]) )
	else:
		sfa_over_node  = mdp.hinet.FlowNode( mdp.Flow([ sfa_node_X, exp_node, sfa_node_Y ]) )

	# upper clone layer
	sfa_upper_layer = mdp.hinet.CloneLayer( sfa_over_node, n_nodes=sfa_switchboard.output_channels )
	
	#-----------------------------------------------------------[ Top Layer(s) ]

	# final sfa master node
	sfa_node_U = mdp.nodes.SFANode				 ( input_dim=sfa_upper_layer.output_dim, output_dim=sfa_dim_red_factor, dtype='float32' )
	exp_node   = mdp.nodes.QuadraticExpansionNode( input_dim=sfa_dim_red_factor )
	noise_node = mdp.nodes.NoiseNode             ( input_dim=exp_node.output_dim, output_dim=exp_node.output_dim, noise_args=(0,numpy.sqrt(0.05)) )
	sfa_node_V = mdp.nodes.SFANode				 ( input_dim=exp_node.output_dim, output_dim=sfa_top_node_out, dtype='float32' )

	if noise:
		sfa_over_node = mdp.hinet.FlowNode( mdp.Flow([ sfa_node_U, exp_node, noise_node, sfa_node_V ]) )	
	else:
		sfa_over_node = mdp.hinet.FlowNode( mdp.Flow([ sfa_node_U, exp_node, sfa_node_V ]) )

	sfa_network = mdp.Flow([ raw_switchboard,
							 sfa_lower_layer,
							 sfa_switchboard,
							 sfa_upper_layer,
							 sfa_over_node  ])
	return sfa_network

def trainNetwork( network, batch_size=None, add_ICA_layer=False, frame_override=None, generic=False ):
	
	# report training parameters
	if add_ICA_layer: print('Adding additional top level ICA node.')
	if generic:       print('Training using generic sequence data.')

	# data file
	try:
		if generic: datafile = open( './current_experiment/sequence_data_generic', 'rb' )
		else:       datafile = open( './current_experiment/sequence_data', 'rb' )
	except:
		print('Error! Required data file could not be opened. Make sure the file')
		print('       was generated via the SFA data converter.')
		sys.exit()

	# data header
	frames       = struct.unpack( 'i', datafile.read(4) )[0]	# no. of image frames
	frame_dim_x  = struct.unpack( 'i', datafile.read(4) )[0]	# width (in px) of a single frame
	frame_dim_y  = struct.unpack( 'i', datafile.read(4) )[0]	# height of a single frame
	raw_data_dim = struct.unpack( 'i', datafile.read(4) )[0]	# color dimension (greyscale/RGB)

	# manual frame override?
	if frame_override != None:
		if frame_override < frames: 
			frames = frame_override
			print('Frame override: training with', frames, 'frames only.')
		else:
			print('Warning! Given frame override value is invalid and will be ignored.')

	# valid batch size?
	if batch_size == None:
		batch_size = frames
	if frames%batch_size != 0:
		print('Error! batch_size does not divide the given frame count evenly!')
		sys.exit()

	# color mode
	if raw_data_dim == 1: print('Color mode is greyscale.')
	if raw_data_dim == 3: print('Color mode is RGB color.')
	if raw_data_dim != 1 and raw_data_dim != 3:
		print('Error! Unknown color mode: ', raw_data_dim)
		return None

	#------------------------------------------------[ Add Sparse Coding Layer ]

	if add_ICA_layer:
		if len(network) == 6: 
			print('Warning! Top ICA layer already part of the network.')
		else:
			top_lvl  = network[ len(network)-1 ]
			ica_node = mdp.nodes.CuBICANode( input_dim=top_lvl.output_dim, dtype='float32' )
			network.append( ica_node )

	#---------------------------------------------------------------[ Get Data ]

	print('Reading training data:', frames, 'frames of', frame_dim_x, 'x', frame_dim_y, 'px images.')

	# read data into memory map
	ping = time.time()
	data = numpy.memmap( 'data_memmap', dtype=numpy.float32, mode='w+', shape=(frames,frame_dim_x*frame_dim_y*raw_data_dim) )

	cnt = 0.0
	for frame in range(0, frames):
		for channel in range(0, frame_dim_x*frame_dim_y*raw_data_dim):
			data[frame,channel] = ord( struct.unpack('c',datafile.read(1))[0] )

		cnt += 1
		done = int(cnt/frames*50.0)
		sys.stdout.write( '\r' + '[READ][' + '='*done + '-'*(50-done) + ']~[' + '%.2f' % (cnt/frames*100.0) + '%]' )
		sys.stdout.flush()
	print('~[%dsec/%dmin]' % (time.time()-ping, (time.time()-ping)/60.0))

	# flush data to disk and reopen memmap in readonly mode
	del data
	data = numpy.memmap( 'data_memmap', dtype=numpy.float32, mode='r', shape=(frames,frame_dim_x*frame_dim_y*raw_data_dim) )

	#-------------------------------------------------------[ Network Training ]

	# batch processing
	if batch_size == frames:
		print('Single file processing: using full data set for single training phase.')
	else:
		print('Batch processing: training %d batches holding %d frames each.' % ( int(data.shape[0]/batch_size), batch_size ))

	ping = time.time()

	# training set data slicers
	training_set = []
	for i in range(4 if generic else len(network)):
		training_set.append( getReusableDataSlicer(data,batch_size) )

	# default training
	if not generic: network.train( training_set )

	# low level training
	else:
		lower_layers = mdp.Flow([ network[0],
								  network[1],
								  network[2],
								  network[3] ])
		lower_layers.train( training_set )

	print('Complete network training time: %dsec / %dmin' % (time.time()-ping, (time.time()-ping)/60.0))
	
	# clean up data by nulling the only reference made
	data = None

	return network


#=======================================================================[ Main ]

def main():

	# check command line arguments
	if '-h' in sys.argv or 'h' in sys.argv or '--help' in sys.argv or 'help' in sys.argv:
		printHelp()
		sys.exit()

	#--------------------------------------------------------------[ Data Info ]

	try:
		if 'generic' in sys.argv: 
			datafile = open( './current_experiment/sequence_data_generic', 'rb' )
		else:
			datafile = open( './current_experiment/sequence_data', 'rb' )
	except:
		print('Error! Required data file could not be opened. Make sure the file')
		print('       was generated via the SFA data converter.')
		sys.exit()

	frames       = struct.unpack( 'i', datafile.read(4) )[0]	# no. of image frames
	frame_dim_x  = struct.unpack( 'i', datafile.read(4) )[0]	# width (in px) of a single frame
	frame_dim_y  = struct.unpack( 'i', datafile.read(4) )[0]	# height of a single frame
	raw_data_dim = struct.unpack( 'i', datafile.read(4) )[0]	# color dimension (greyscale/RGB)

	#----------------------------------------------------[ Training Parameters ]

	use_wide_fov = True if frame_dim_x==320 else False
	use_color    = True if raw_data_dim==3  else False

	generic        = 'generic' in sys.argv
	noisy_nodes    = ('noise' in sys.argv)
	add_ICA        =  ('ICA' in sys.argv)

	batch_size     = None
	frame_override = None
	tsn_file       = None
	for i, arg in enumerate(sys.argv):
		if arg == 'batch_size': batch_size     = int(sys.argv[i+1])
		if arg == 'frames':     frame_override = int(sys.argv[i+1])
		if arg == 'file':       tsn_file       = sys.argv[i+1]

	#---------------------------------------------------------[ Set Up Network ]

	if 'file' in sys.argv:
		# filename shortcut?
		if tsn_file == '-':
			for f in os.listdir( './current_experiment' ):
				if '.tsn' in f: tsn_file = f
		if tsn_file == '-':
			print('Error! No .tsn file was found in folder \'./current_experiment\'.')
		# open file
		try:
			print('Loading network from file \'%s\'' % tsn_file)
			network = open( './current_experiment/'+tsn_file, 'r' )
		except:
			print('Error opening SFA network file.')
			sys.exit()
		# extract network
		network    = pickle.load( network )
		if add_ICA:
			tsn_file  = tsn_file[:len(tsn_file)-4]
			tsn_file += '_ICA.tsn'

	# initialize new network
	else:
		network = initNetwork( wide_fov = use_wide_fov,
							   color    = use_color,
							   noise    = noisy_nodes )

	print('Network state before training:')
	printNetworkState( network )

	#---------------------------------------------------------------[ Training ]

	trainNetwork( network, batch_size, add_ICA, frame_override, generic )

	print('\nNetwork state after training:')
	printNetworkState( network )

	#--------------------------------------------------------[ Save and Return ]

	filename = tsn_file

	if filename == None:
		filename = 'network_x' + ( str(frame_override) if frame_override != None else str(frames) )
		if generic:       filename += '_generic'
		if use_color:     filename += '_color'
		else:             filename += '_greyscale'
		if noisy_nodes:   filename += '_noise'
		if add_ICA:       filename += '_ICA'
		filename += '.tsn'
	
	network.save( ('./current_experiment/'+filename) )
	print('Trained SFA network stored to file \'./current_experiment/%s\'' % filename)

#-----------------------------------------------------------------------[ Help ]

def printHelp():
	print('================================================================================')
	print('RatLab training help                                                            ')
	print('--------------------------------------------------------------------------------')
	print('This program trains a SFA hierarchy network and stores the trained network as a')
	print('.tsn file (Trained Sfa Network) to disk under the default name:')
	print('  \'network_xSTEPS_MODE.tsn\'')
	print('Where STEPS denotes the number of input samples the network was trained with,')
	print('and MODE is either \'color\' or \'greyscale\' to indicate which kind of input')
	print('data the network expects when used for sampling. These parameters are read ')
	print('directly from the input data, which this program assumes to be found within an')
	print('existing \'sequence_data\' file that was previously generated by convert.py.\n')
	print('--------------------------------------------------------[ Command Line Options ]\n')
	print('batch_size <count>')
	print('          If specified, the network will be trained with batches of data instead')
	print('          of using all available data at once. Note that <count> has to evenly')
	print('          divide the number of frames being used to train the network!\n')
	print('frames <n>')
	print('          If specified, the network will be trained with <n> frames only, even if')
	print('          the sequence data file contains additional frames. This can be used to')
	print('          record <x> frames and train various networks with <x-y> frames to see')
	print('          the difference made by the additional <y> frames.\n')
	print('ICA       This optional parameter tells the network to add an additional layer of')
	print('          sparse coding (implemented via an ICA node) at the top of the network.\n')
	print('noise     This optional parameter tells the network to inlude additional nodes')
	print('          that add random noise to the processed data. This may help in case')
	print('          the trainig phase crashes due to singular matrices. (Note: this may')
	print('          also be helped by training with more data, i.e., moretime steps.) If')
	print('          no custom file name is provided, the default filename is extended by')
	print('          a \'_noise\' tag.\n')
	print('---------------------------------------------------[ Advanced Training Options ]\n')
	print('generic   (...)\n')
	print('add_ICA <file>')
	print('          If this parameter is set, no new network is being trained. Instead')
	print('          <file> is expected to be the name of a .tsn file that contains a')
	print('          network which already has been trained beforehand but does not yet')
	print('          include an additional ICA layer. The network will be extended by an')
	print('          additional ICA node which is then trained as usual. The resulting')
	print('          network will be stored in a new file using the original name plus an')
	print('          additional \'_ICA\' suffix.')
	print('          NOTE: The filename can be replaced by a simple \'-\' in which case the')
	print('          first found .tsn file in the \'current_experiment\' folder will be used.\n')
	print('--------------------------------------------------------------------[ Examples ]\n')
	print('Train the network with an additional sparse coding step and store it as \'data.tsn\'')
	print('     $ python train.py sparse file data.tsn')
	print('================================================================================')

main() # <<<   <<<   <<<   <<<   <<<   <<<   <<<   <<<   <<<   <<<   <<<[ main ]
