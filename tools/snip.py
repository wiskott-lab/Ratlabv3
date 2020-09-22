

#=====================================================================[ Header ]

# system
import os
import sys
import time
import types

# math
import numpy
import math

# graphics
import Image
import ImageDraw

#-----------------------------------------------------------------[ Crop Areas ]

DEF_CROP_WIDE_DEFAULT = DEF_CROP_NARROW_DEFAULT = DEF_CROP_WIDEx2_UPPER = \
DEF_CROP_WIDEx2_LOWER = DEF_CROP_NARROWx2_UPPER = DEF_CROP_NARROWx2_LOWER = \
DEF_CROP_WIDEx3_UPPER = DEF_CROP_WIDEx3_CENTER = DEF_CROP_WIDEx3_LOWER = \
DEF_CROP_NARROWx3_UPPER = DEF_CROP_NARROWx3_CENTER = DEF_CROP_NARROWx3_LOWER = None

def setGlobals( frame_dim ):

	### print ('Frame size for next folder:', frame_dim)

	global DEF_CROP_WIDE_DEFAULT;    DEF_CROP_WIDE_DEFAULT    = ( frame_dim[0]/2-160, frame_dim[1]/2-20, frame_dim[0]/2+160, frame_dim[1]/2+20 )
	global DEF_CROP_NARROW_DEFAULT;  DEF_CROP_NARROW_DEFAULT  = ( frame_dim[0]/2- 27, frame_dim[1]/2-17, frame_dim[0]/2+ 28, frame_dim[1]/2+18 )

	global DEF_CROP_WIDEx2_UPPER;    DEF_CROP_WIDEx2_UPPER    = ( frame_dim[0]/2-160, frame_dim[1]/2-40, frame_dim[0]/2+160, frame_dim[1]/2 )
	global DEF_CROP_WIDEx2_LOWER;    DEF_CROP_WIDEx2_LOWER    = ( frame_dim[0]/2-160, frame_dim[1]/2, frame_dim[0]/2+160, frame_dim[1]/2+40 )

	global DEF_CROP_NARROWx2_UPPER;  DEF_CROP_NARROWx2_UPPER  = ( frame_dim[0]/2-27, frame_dim[1]/2-35, frame_dim[0]/2+28, frame_dim[1]/2 )
	global DEF_CROP_NARROWx2_LOWER;  DEF_CROP_NARROWx2_LOWER  = ( frame_dim[0]/2-27, frame_dim[1]/2, frame_dim[0]/2+28, frame_dim[1]/2+35 )

	global DEF_CROP_WIDEx3_UPPER;    DEF_CROP_WIDEx3_UPPER    = ( frame_dim[0]/2-160, frame_dim[1]/2-60, frame_dim[0]/2+160, frame_dim[1]/2-20 )
	global DEF_CROP_WIDEx3_CENTER;   DEF_CROP_WIDEx3_CENTER   = ( frame_dim[0]/2-160, frame_dim[1]/2-20, frame_dim[0]/2+160, frame_dim[1]/2+20 )
	global DEF_CROP_WIDEx3_LOWER;    DEF_CROP_WIDEx3_LOWER    = ( frame_dim[0]/2-160, frame_dim[1]/2+20, frame_dim[0]/2+160, frame_dim[1]/2+60 )

	global DEF_CROP_NARROWx3_UPPER;  DEF_CROP_NARROWx3_UPPER  = ( frame_dim[0]/2-27, frame_dim[1]/2-52, frame_dim[0]/2+28, frame_dim[1]/2-17 )
	global DEF_CROP_NARROWx3_CENTER; DEF_CROP_NARROWx3_CENTER = ( frame_dim[0]/2-27, frame_dim[1]/2-17, frame_dim[0]/2+28, frame_dim[1]/2+18 )
	global DEF_CROP_NARROWx3_LOWER;  DEF_CROP_NARROWx3_LOWER  = ( frame_dim[0]/2-27, frame_dim[1]/2+18, frame_dim[0]/2+28, frame_dim[1]/2+53 )


#=======================================================================[ Main ]

def main():

	# halp
	if '-h' in sys.argv or 'h' in sys.argv or '--help' in sys.argv or 'help' in sys.argv:
		printHelp()
		sys.exit()

	# setup
	sequence_folder = './sequence_generic/'
	frame_folders   = []
	frame_grab      = 'wide'
	multiplier      = 1
	data_cap        = None

	if os.path.isdir(sequence_folder) == False:
		try:    os.mkdir(sequence_folder)
		except: print('Missing destination folder!', sys.exit())

	# parameter
	for i, arg in enumerate( sys.argv ):
		if i == 0: continue
		elif arg == 'x2': multiplier = 2
		elif arg == 'x3': multiplier = 3
		elif arg == 'narrow_frame_grab': frame_grab = 'narrow'
		elif arg == 'cap': data_cap = int(sys.argv[i+1]); break 
		else: frame_folders.append( arg )

	print('Frame grab:', frame_grab)
	print('List of folders:', frame_folders)

	frame_count = 0
	for folder in frame_folders: frame_count += len(os.listdir(folder))
	print('No. of frames in all folders:', frame_count)

	if multiplier != 1: print('Frame data multiplier: x%d' % multiplier)
	if data_cap: print('Data cap (%d/%d)' % (data_cap, frame_count*multiplier))

	# extracting frame data
	count = 0
	stahp = False

	for n in range(multiplier):
		for source_folder in frame_folders:

			img_sequence = os.listdir( source_folder )
			img_sequence.sort()

			setGlobals( Image.open(str(source_folder+'/'+img_sequence[0])).size )
			
			for source_frame in img_sequence:
				try:
					frame = Image.open( str(source_folder+'/'+source_frame) )
				except:
					print('\nWarning! Skipping inaccessible file', str(source_folder+'/'+source_frame))
					continue

				if frame_grab == 'wide':
					if multiplier == 1:
						frame.crop( DEF_CROP_WIDE_DEFAULT ).save( sequence_folder+'frame_'+str(count).zfill(5)+'.png' )
					if multiplier == 2:
						if n==0: frame.crop( DEF_CROP_WIDEx2_UPPER ).save( sequence_folder+'frame_'+str(count).zfill(5)+'.png' )
						if n==1: frame.crop( DEF_CROP_WIDEx2_LOWER ).save( sequence_folder+'frame_'+str(count).zfill(5)+'.png' )
					if multiplier == 3:
						if n==0: frame.crop( DEF_CROP_WIDEx3_UPPER  ).save( sequence_folder+'frame_'+str(count).zfill(5)+'.png' )
						if n==1: frame.crop( DEF_CROP_WIDEx3_CENTER ).save( sequence_folder+'frame_'+str(count).zfill(5)+'.png' )
						if n==2: frame.crop( DEF_CROP_WIDEx3_LOWER  ).save( sequence_folder+'frame_'+str(count).zfill(5)+'.png' )

				if frame_grab == 'narrow':
					if multiplier == 1:
						frame.crop( DEF_CROP_NARROW_DEFAULT ).save( sequence_folder+'frame_'+str(count).zfill(5)+'.png' )
					if multiplier == 2:
						if n==0: frame.crop( DEF_CROP_NARROWx2_UPPER ).save( sequence_folder+'frame_'+str(count).zfill(5)+'.png' )
						if n==1: frame.crop( DEF_CROP_NARROWx2_LOWER ).save( sequence_folder+'frame_'+str(count).zfill(5)+'.png' )
					if multiplier == 3:
						if n==0: frame.crop( DEF_CROP_NARROWx3_UPPER  ).save( sequence_folder+'frame_'+str(count).zfill(5)+'.png' )
						if n==1: frame.crop( DEF_CROP_NARROWx3_CENTER ).save( sequence_folder+'frame_'+str(count).zfill(5)+'.png' )
						if n==2: frame.crop( DEF_CROP_NARROWx3_LOWER  ).save( sequence_folder+'frame_'+str(count).zfill(5)+'.png' )

				count += 1

				# housekeeping					
				done = int(count/float(frame_count*multiplier if not data_cap else data_cap)*50.0)
				sys.stdout.write( '\r' + '[' + '='*done + '-'*(50-done) + ']~[' + '%.2f' % (count/float(frame_count*multiplier if not data_cap else data_cap)*100.0) + '%]' )
				sys.stdout.flush()

				if data_cap and count == data_cap:
					print('\nData cap reached.')
					stahp = True
					break

			if stahp: break
		if stahp: break
	print('')

	# check for cap reached
	if count < data_cap:
		print('Warning: Set data cap was not reached (%d/%d).' % (count, data_cap))

#-----------------------------------------------------------------------[ Help ]

def printHelp():
	print('================================================================================')
	print('Snipping Tool Help                                                              ')
	print('--------------------------------------------------------------------------------')
	print('This program goes through a number of provided folders, assumed to be filled')
	print('images. From those the center area is cut out and stored in a destination folder')
	print('for further use as generic training material for ratlab.\n')
	print('--------------------------------------------------------[ Command Line Options ]\n')
	print('<list of folders>')
	print('          Each parameter not listed below is assumed to name a folder filled')
	print('          with images to extract image data from.\n')
	print('narrow_frame_grab')
	print('          By default, the center area (320x40) of each source image is extracted')
	print('          and stored in the destination folder \'sequence_generic\'. If this')
	print('          parameter is set, however, the extracted area is changed to a more')
	print('          narrow window of 55x35 pixels. Both sets of dimensions correspond to')
	print('          the two possible input data formats expected by the ratlab pipeline.\n')
	print('cap <limit>')
	print('          This parameter allows to set a limit for the number of extraced')
	print('          frames.')
	print('          NOTE: This parameter is set last, i.e., later parameters will be')
	print('          ignored!\n')
	print('x2        If this parameter is set, two rectangular areas are extracted from')
	print('          each frame.')
	print('x3        If this parameter is set, three rectangular areas are extracted from')
	print('          each frame.\n')
	print('--------------------------------------------------------------------[ Examples ]\n')
	print('Extract center areas of all the images listed in two test folders:')
	print('     $ python snip.py test_folder_1 test_folder_2')
	print('Extract twice the data, but no more than 100k frame grabs:')
	print('     $ python snip.py test_folder_1 test_folder_2 x2 cap 100000')
	print('================================================================================')

main() # <<<   <<<   <<<   <<<   <<<   <<<   <<<   <<<   <<<   <<<   <<<[ main ]
