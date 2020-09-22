
#=====================================================================[ Header ]

# system
import sys

# PIL
from PIL import Image as mod_img

# graphics
from OpenGL.GLUT import *
from OpenGL.GLU  import *
from OpenGL.GL   import *

#--------------------------------------------[ opengl texture loading function ]

def loadTextureRGBA( filename, mipmapping=False ):
		# open image
		src_img = mod_img.open( filename )
		img_str = src_img.tobytes( 'raw', 'RGBA', 0, -1 )
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
							   4,
							   src_img.size[0], 
							   src_img.size[1], 
							   GL_RGBA, 
							   GL_UNSIGNED_BYTE, 
							   img_str )
		else:
			glTexImage2D( GL_TEXTURE_2D,    # target
            	          0,                # mipmap level
            	          4,                # color components (3: rgb, 4: rgba)
            	          src_img.size[0],  # texture width
            	          src_img.size[1],  # texture height
            	          0,                # border
            	          GL_RGBA,          # format
        	              GL_UNSIGNED_BYTE, # data type
            	          img_str )         # texture data
		# return handle id
		return int(img_id)

def loadTextureRGB( filename, mipmapping=False ):
		# open image
		src_img = mod_img.open( filename )
		img_str = src_img.tostring( 'raw', 'RGB', 0, -1 )
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
							   GL_RGBA, 
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
		