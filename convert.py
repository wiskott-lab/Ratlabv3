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
import struct

# math
import math
import numpy  as np

# python image library
from PIL import Image
from PIL import ImageDraw


#====================================================================[ Convert ]

def convert( data_folder, data_file ):

    # datafile
    datafile = open( data_file, 'wb' )

    # input file sequence
    img_sequence = os.listdir( data_folder )
    img_sequence.sort()

    # data header
    frame = Image.open( (data_folder + img_sequence[0]) )

    color_dim = None
    if frame.mode == 'RGBA' or frame.mode == 'RGB':
        print('Color mode is RGB.')
        color_dim = 3
    elif frame.mode == 'L':
        print('Color mode is greyscale.')
        color_dim = 1
    else:
        print('Error! Unknown color mode \'%s\'!' % frame.mode)
        return False

    header = struct.pack( 'iiii', len(img_sequence), # how many frames in the sequence
                                  frame.size[0],     # width of a single frame
                                  frame.size[1],     # height of a single frame
                                  color_dim )        # color dimension (greyscale/RGB)
    datafile.write( header )

    # file info
    space_req  = float(frame.size[0]*frame.size[1]*len(img_sequence)) / (1024.0*1024.0)
    space_req *= color_dim
    print('Writing data to file \'%s\'. Expected size: %.1f megabytes.' % (data_file, space_req))      # color values are only stored as characters

    # data loop
    cnt = 0.0
    for filename in img_sequence:

        try:
            frame_file = Image.open( (data_folder + filename) )
            frame_data = frame_file.load()
        except:
            print('\nfailed', filename)
            sys.exit()

        for y in range(0, frame_file.size[1]):
            for x in range(0, frame_file.size[0]):
                if color_dim == 3:
                    datafile.write( struct.pack('c',bytes([frame_data[x,y][0]])))
                    datafile.write( struct.pack('c',bytes([frame_data[x,y][1]])))
                    datafile.write( struct.pack('c',bytes([frame_data[x,y][2]])))
                else:
                    datafile.write( struct.pack('c',bytes([frame_data[x,y]])))

        # progress
        cnt += 1.0
        done = int( cnt/len(img_sequence)*50.0 )
        sys.stdout.write( '\r' + '[' + '='*done + '-'*(50-done) + ']~[' + '%.2f' % (cnt/len(img_sequence)*100.0) + '%]' )
        sys.stdout.flush()

    print('\nAll done.')


#=======================================================================[ Main ]

def main():
    
    # check command line arguments
    if len(sys.argv) > 1:
        print('Warning: convert.py does not accept any command line options!')

    if '-h' in sys.argv or 'h' in sys.argv or '--help' in sys.argv or 'help' in sys.argv:
        printHelp()
        sys.exit()

    # convert simulation data
    if os.path.isdir('./current_experiment/sequence/') == True:
        convert( './current_experiment/sequence/', 
                 './current_experiment/sequence_data' )

    # convert generic training data if available
    if os.path.isdir('./current_experiment/sequence_generic/') == True:
        convert( './current_experiment/sequence_generic/', 
                 './current_experiment/sequence_data_generic' )

#-----------------------------------------------------------------------[ Help ]

def printHelp():
	print('================================================================================')
	print('RatLab convert help                                                             ')
	print('--------------------------------------------------------------------------------')
	print('This program reads an image sequence located in ./sequence and produces a data  ')
	print('file that is formatted for immediate use with an SFA hierachy. The image data is')
	print('not formatted in any special way, but simply strictly written to file: Each line')
	print('contains the color information of a single frame.')
	print('The data is preceded by a header consisting of the following integer values:')
	print('  (1) frames: how many images there are in the full sequence')
	print('  (2) width:  the width in pixels of a single frame')
	print('  (3) height: the height in pixels of a single frame')
	print('  (4) color:  the color dimension (i.e., 1 for greyscale, and 3 for RGB color)\n')
	print('================================================================================')

main() # <<<   <<<   <<<   <<<   <<<   <<<   <<<   <<<   <<<   <<<   <<<[ main ]

