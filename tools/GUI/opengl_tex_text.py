#=====================================================================[ Header ]

#system
import sys
sys.path.append( './util' )

# math
import math

# python image library
from PIL import Image as img

# OpenGL
from OpenGL.GLUT import *
from OpenGL.GLU  import *
from OpenGL.GL   import *

# font setup
from opengl_texture_load import *
FONT_TEX   = 0
FONT_WIDTH = 26 # actually 32 but 26 looks nicer

def __drawCharacter__( c ):
	"""
	Font texture: 512x512 w/ 16x16 characters
	"""
	# basic character offset
	x = 0.0625
	y = 0.0625
	# character indices
	if c == ' ': return
	# large cap letters
	elif c == 'A': 	x *=  1.0;  y *= 11.0;
	elif c == 'B': 	x *=  2.0;  y *= 11.0;
	elif c == 'C': 	x *=  3.0;  y *= 11.0;
	elif c == 'D': 	x *=  4.0;  y *= 11.0;
	elif c == 'E': 	x *=  5.0;  y *= 11.0;
	elif c == 'F': 	x *=  6.0;  y *= 11.0;
	elif c == 'G': 	x *=  7.0;  y *= 11.0;
	elif c == 'H': 	x *=  8.0;  y *= 11.0;
	elif c == 'I': 	x *=  9.0;  y *= 11.0;
	elif c == 'J': 	x *= 10.0;  y *= 11.0;
	elif c == 'K': 	x *= 11.0;  y *= 11.0;
	elif c == 'L': 	x *= 12.0;  y *= 11.0;
	elif c == 'M': 	x *= 13.0;  y *= 11.0;
	elif c == 'N': 	x *= 14.0;  y *= 11.0;
	elif c == 'O': 	x *= 15.0;  y *= 11.0;
	elif c == 'P': 	x *=  0.0;  y *= 10.0;
	elif c == 'Q': 	x *=  1.0;  y *= 10.0;
	elif c == 'R': 	x *=  2.0;  y *= 10.0;
	elif c == 'S': 	x *=  3.0;  y *= 10.0;
	elif c == 'T': 	x *=  4.0;  y *= 10.0;
	elif c == 'U': 	x *=  5.0;  y *= 10.0;
	elif c == 'V': 	x *=  6.0;  y *= 10.0;
	elif c == 'W': 	x *=  7.0;  y *= 10.0;
	elif c == 'X': 	x *=  8.0;  y *= 10.0;
	elif c == 'Y': 	x *=  9.0;  y *= 10.0;
	elif c == 'Z': 	x *= 10.0;  y *= 10.0;
	# small cap letters
	elif c == 'a': 	x *=  1.0;  y *= 9.0;
	elif c == 'b': 	x *=  2.0;  y *= 9.0;
	elif c == 'c': 	x *=  3.0;  y *= 9.0;
	elif c == 'd': 	x *=  4.0;  y *= 9.0;
	elif c == 'e': 	x *=  5.0;  y *= 9.0;
	elif c == 'f': 	x *=  6.0;  y *= 9.0;
	elif c == 'g': 	x *=  7.0;  y *= 9.0;
	elif c == 'h': 	x *=  8.0;  y *= 9.0;
	elif c == 'i': 	x *=  9.0;  y *= 9.0;
	elif c == 'j': 	x *= 10.0;  y *= 9.0;
	elif c == 'k': 	x *= 11.0;  y *= 9.0;
	elif c == 'l': 	x *= 12.0;  y *= 9.0;
	elif c == 'm': 	x *= 13.0;  y *= 9.0;
	elif c == 'n': 	x *= 14.0;  y *= 9.0;
	elif c == 'o': 	x *= 15.0;  y *= 9.0;
	elif c == 'p': 	x *=  0.0;  y *= 8.0;
	elif c == 'q': 	x *=  1.0;  y *= 8.0;
	elif c == 'r': 	x *=  2.0;  y *= 8.0;
	elif c == 's': 	x *=  3.0;  y *= 8.0;
	elif c == 't': 	x *=  4.0;  y *= 8.0;
	elif c == 'u': 	x *=  5.0;  y *= 8.0;
	elif c == 'v': 	x *=  6.0;  y *= 8.0;
	elif c == 'w': 	x *=  7.0;  y *= 8.0;
	elif c == 'x': 	x *=  8.0;  y *= 8.0;
	elif c == 'y': 	x *=  9.0;  y *= 8.0;
	elif c == 'z': 	x *= 10.0;  y *= 8.0;
	# special characters
	elif c == '>': x *= 15.0; y *= 5.0;
	elif c == '!': x *=  1.0; y *= 13.0;
	elif c == '?': x *= 15.0; y *= 12.0;
	elif c == '/': x *= 15.0; y *= 13.0;
	elif c == '\\':x *= 12.0; y *= 10.0;
	elif c == '.': x *= 14.0; y *= 13.0;
	elif c == ',': x *= 12.0; y *= 13.0;
	elif c == ':': x *= 10.0; y *= 12.0;
	elif c == '_': x *= 15.0;  y *= 10.0;
	# mathematical
	elif c == '+': x *= 11.0; y *= 13.0;
	elif c == '-': x *= 13.0; y *= 13.0;
	elif c == '*': x *= 10.0; y *= 13.0;
	elif c == '=': x *= 13.0; y *= 12.0;
	# parantheses
	elif c == '(': x *=  8.0; y *= 13.0;
	elif c == ')': x *=  9.0; y *= 13.0;
	elif c == '[': x *= 11.0; y *= 10.0;
	elif c == ']': x *= 13.0; y *= 10.0;
	# numbers
	elif c == '0': x *= 0.0; y *= 12.0;
	elif c == '1': x *= 1.0; y *= 12.0;
	elif c == '2': x *= 2.0; y *= 12.0;
	elif c == '3': x *= 3.0; y *= 12.0;
	elif c == '4': x *= 4.0; y *= 12.0;
	elif c == '5': x *= 5.0; y *= 12.0;
	elif c == '6': x *= 6.0; y *= 12.0;
	elif c == '7': x *= 7.0; y *= 12.0;
	elif c == '8': x *= 8.0; y *= 12.0;
	elif c == '9': x *= 9.0; y *= 12.0;
	# texture drawing
	glTexCoord2f( x, y )
	glVertex2i( 0,0 )
	glTexCoord2f( x+0.0625, y )
	glVertex2i( 32,0 )
	glTexCoord2f( x+0.0625, y+0.0625 )
	glVertex2i( 32,32 )
	glTexCoord2f( x, y+0.0625 )
	glVertex2i( 0,32 )

def drawString( string, pos, scale=None ):
	# first call
	global FONT_TEX
	if FONT_TEX == 0:
		FONT_TEX = loadTextureRGBA( './tools/GUI/font.png' )
	# setup
	glPushMatrix()
	glTranslate( pos[0], pos[1], 0 )
	if scale != None:
		glScale( scale, scale, scale )
	glBindTexture( GL_TEXTURE_2D, FONT_TEX )
	# draw
	for c in string:
		glBegin( GL_QUADS )
		__drawCharacter__(c)
		glEnd()
		glTranslate( FONT_WIDTH,0,0 )
	# reset
	glPopMatrix()
