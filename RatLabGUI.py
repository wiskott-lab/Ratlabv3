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

# math
import numpy as np

# python image library
from PIL import Image as IMG

# OpenGL
from OpenGL.GLUT import *
from OpenGL.GLU  import *
from OpenGL.GL   import *

# utilities / own
sys.path.append( './tools/GUI' )
import opengl_tex_text     as TXT
import opengl_texture_load as TEX

# font size in px
FONT_WIDTH = 26


#============================================================[ Utility Classes ]

import freezeable
Freezeable = freezeable.Freezeable

class TextureLib( Freezeable ):
  def __init__(self):
    self.background   = TEX.loadTextureRGBA( './tools/GUI/gui_background.png' )
    self.cursor       = TEX.loadTextureRGBA( './tools/GUI/cursor.png' )
    self.cross        = TEX.loadTextureRGBA( './tools/GUI/cross.png' )
    self.tick_nay     = TEX.loadTextureRGBA( './tools/GUI/tick_nay.png' )
    self.tick_yay     = TEX.loadTextureRGBA( './tools/GUI/tick_yay.png' )
    self.font         = TEX.loadTextureRGBA( './tools/GUI/font.png' )
    self.button       = TEX.loadTextureRGBA( './tools/GUI/script_button.png' )
    self.param_box    = TEX.loadTextureRGBA( './tools/GUI/param_box.png' )
    self.param_circle = TEX.loadTextureRGBA( './tools/GUI/param_circle.png' )
    self.param_custom = TEX.loadTextureRGBA( './tools/GUI/param_custom.png' )
    self.param_star   = TEX.loadTextureRGBA( './tools/GUI/param_star.png' )
    self.param_T      = TEX.loadTextureRGBA( './tools/GUI/param_t-maze.png' )
    self.freeze()

#----------------------------------------------------------------[ gui control ]

class Ctrl( Freezeable ):
  def __init__(self):
    # textures
    self.tex_lib = TextureLib()
    # buttons
    self.def_buttons = []
    self.def_buttons.append( Button(( 48,100),(27,27),self.tex_lib.cross,tag='box'   ) )    # box maze
    self.def_buttons.append( Button((108,100),(27,27),self.tex_lib.cross,tag='star'  ) )    # star maze
    self.def_buttons.append( Button((183,100),(27,27),self.tex_lib.cross,tag='t'     ) )    # T-maze
    self.def_buttons.append( Button((243,100),(27,27),self.tex_lib.cross,tag='circle') )    # circle maze
    self.def_buttons.append( Button((308,100),(27,27),self.tex_lib.cross,tag='custom') )    # custom maze / file
    self.def_buttons.append( ButtonT((840,80),(158,77),self.tex_lib.button,tag='script'))   # script button
    # default text fields
    self.def_fields = []
    self.def_fields.append( TextField((400,50),number=True) )    # 0:  frames
    self.def_fields.append( TextField((780,150),number=True) )   # 1:  training - batch size
    self.def_fields.append( TextField((780,200),number=True) )   # 2:  training - frames
    self.def_fields.append( TickBox((780,250)) )                 # 3:  training - +ica
    self.def_fields.append( TickBox((780,300)) )                 # 4:  training - +noise
    self.def_fields.append( TextField((190,477),number=True) )   # 6:  rat - speed
    self.def_fields.append( TextField((440,477),number=True) )   # 7:  rat - momentum
    self.def_fields.append( TextField((680,477),number=True) )   # 8:  rat - dec_arc
    self.def_fields.append( TickBox((925,475)) )                 # 9:  rat - small_fov
    self.def_fields.append( TickBox((925,525)) )                 # 10: rat - path_loop
    self.def_fields.append( TextField((190,525)) )               # 11: rat - path file
    # parameter fields
    self.box_fields = []
    self.box_fields.append( TextField((220,150),number=True) )    # 0: length
    self.box_fields.append( TextField((220,200),number=True) )    # 1: width
    self.box_fields.append( TextField((220,250),number=True) )    # 2: height
    self.circle_fields = []
    self.circle_fields.append( TextField((220,150),number=True) )    # 0: radius
    self.circle_fields.append( TextField((220,200),number=True) )    # 1: segments
    self.circle_fields.append( TextField((220,250),number=True) )    # 2: height
    self.custom_fields = []
    self.custom_fields.append( TextField((220,150)) )    # file name
    self.star_fields = []
    self.star_fields.append( TextField((220,150),number=True) )    # 0: arms
    self.star_fields.append( TextField((220,200),number=True) )    # 1: arm width
    self.star_fields.append( TextField((220,250),number=True) )    # 2: arm length
    self.star_fields.append( TextField((220,300),number=True) )    # 3: arm height
    self.t_fields = []
    self.t_fields.append( TextField((220,150),number=True) )    # 0: vert. length
    self.t_fields.append( TextField((220,200),number=True) )    # 1: vert. width
    self.t_fields.append( TextField((220,250),number=True) )    # 2: horz. length
    self.t_fields.append( TextField((220,300),number=True) )    # 3: horz. width
    self.t_fields.append( TextField((220,350),number=True) )    # 4: wall height
    # field management
    self.act_param  = 'box'
    self.act_field  = None
    self.def_buttons[0].act = True
    self.txt_fields = [] + self.def_buttons + self.def_fields + self.box_fields
    # lockdown
    self.freeze()
ctrl = None

#---------------------------------------------------------------------[ button ]

class ButtonT( Freezeable ):
  def __init__( self, pos, dim, texture=None, tag=None ):
    self.pos = (pos[0],550-pos[1])
    self.dim = dim
    self.tex = texture
    self.tag = tag
    self.act = False
    self.freeze()
  def select(self, x, y):
    if x >= self.pos[0]-2 and x <= self.pos[0]+self.dim[0]+2 and \
       y >= self.pos[1]-2 and y <= self.pos[1]+self.dim[1]+2:
       self.act = not self.act
    return self.act
  def display(self):
    if self.tex == None: pass
    else:
      glBindTexture( GL_TEXTURE_2D, self.tex )
      glBegin( GL_QUADS )
      glTexCoord2f( 0.0, 0.0 )
      glVertex2i( self.pos[0], self.pos[1] )
      glTexCoord2f( 1.0, 0.0 )
      glVertex2i( self.pos[0]+self.dim[0], self.pos[1] )
      glTexCoord2f( 1.0, 1.0 )
      glVertex2i( self.pos[0]+self.dim[0], self.pos[1]+self.dim[1] )
      glTexCoord2f( 0.0, 1.0 )
      glVertex2i( self.pos[0], self.pos[1]+self.dim[1] )
      glEnd()
  def input(self,c): pass

class Button( Freezeable ):
  def __init__( self, pos, dim, texture=None, tag=None ):
    self.pos = (pos[0],550-pos[1])
    self.dim = dim
    self.tex = texture
    self.tag = tag
    self.act = False
    self.freeze()
  def select(self, x, y):
    if x >= self.pos[0]-2 and x <= self.pos[0]+self.dim[0]+2 and \
       y >= self.pos[1]-2 and y <= self.pos[1]+self.dim[1]+2:
       self.act = not self.act
    return self.act
  def display(self):
    if self.tex == None: pass
    elif self.act:
      glBindTexture( GL_TEXTURE_2D, self.tex )
      glBegin( GL_QUADS )
      glTexCoord2f( 0.0, 0.0 )
      glVertex2i( self.pos[0]-3, self.pos[1] )
      glTexCoord2f( 1.0, 0.0 )
      glVertex2i( self.pos[0]+self.dim[0]+3, self.pos[1] )
      glTexCoord2f( 1.0, 1.0 )
      glVertex2i( self.pos[0]+self.dim[0]+3, self.pos[1]+self.dim[1]+3 )
      glTexCoord2f( 0.0, 1.0 )
      glVertex2i( self.pos[0]-3, self.pos[1]+self.dim[1]+3 )
      glEnd()
  def input(self,c): pass
 
#-------------------------------------------------------------------[ tick box ]

class TickBox( Freezeable ):
  def __init__( self, pos ):
    self.pos  = (pos[0],550-pos[1])
    self.tick = False
    self.freeze()
  def display(self):
    glPushMatrix()
    glTranslate( self.pos[0], self.pos[1], 0 )
    if self.tick:  glBindTexture( GL_TEXTURE_2D, ctrl.tex_lib.tick_yay )
    else:          glBindTexture( GL_TEXTURE_2D, ctrl.tex_lib.tick_nay )
    glBegin( GL_QUADS )
    glTexCoord2f( 0.0, 0.0 )
    glVertex2i( 0,0 )
    glTexCoord2f( 1.0, 0.0 )
    glVertex2i( 32,0 )
    glTexCoord2f( 1.0, 1.0 )
    glVertex2i( 32,32 )
    glTexCoord2f( 0.0, 1.0 )
    glVertex2i( 0,32 )
    glEnd()
    glPopMatrix()
  def select(self, x, y):
    if x >= self.pos[0]-3 and x <= self.pos[0]+35 and \
       y >= self.pos[1]-3 and y <= self.pos[1]+35:
       self.tick = not self.tick
       return self.tick
  def input(self,char):
    pass

#-----------------------------------------------------------------[ text field ]

class TextField( Freezeable ):
  def __init__( self, pos, number=False ):
    self.number = number
    self.pos    = (pos[0],550-pos[1])
    self.text   = '-'
    self.dot    = False
    self.active = False
    self.freeze()
  def display(self):
    TXT.drawString( self.text, self.pos )
    # cursor
    if self.active:
      glPushMatrix()
      glTranslate( self.pos[0]+len(self.text)*FONT_WIDTH+2, self.pos[1]-2, 0 )
      glBindTexture( GL_TEXTURE_2D, ctrl.tex_lib.cursor )
      glBegin( GL_QUADS )
      glTexCoord2f( 0.0, 0.0 )
      glVertex2i( 0,0 )
      glTexCoord2f( 1.0, 0.0 )
      glVertex2i( 7,0 )
      glTexCoord2f( 1.0, 1.0 )
      glVertex2i( 7,35 )
      glTexCoord2f( 0.0, 1.0 )
      glVertex2i( 0,35 )
      glEnd()
      glPopMatrix()
  def input(self, char):    
    if self.number == False:
      # backspace: delete character
      if char == None:
        if len(self.text) > 0:
          self.text = self.text[:-1]
      # add to string
      else:
        self.text += str(char)
    else:
      # backspace: delete character
      if char == None:
        if len(self.text) > 0:
          self.text = self.text[:-1]
          if '.' not in self.text and self.dot == True: self.dot = False
      # digit input
      elif char.isdigit() or char == '.':
        # start new digit
        if '-' in self.text:
          self.text = str(char)
        # add to digit
        elif char.isdigit():
          self.text += str(char)
        # floating point point
        elif char == '.':
          if self.dot: return
          else:
            self.dot     = True
            self.text   += str(char)
  def getNumber(self,integer=False):
    if self.dot:
      return float(self.text) if not integer else None
    else:
      return int(self.text)
  def select(self, x, y):
    if x >= self.pos[0] and x < self.pos[0]+FONT_WIDTH*len(self.text) and \
       y >= self.pos[1] and y < self.pos[1]+FONT_WIDTH:
       self.active = True
    else:
      self.active = False
      if len(self.text) == 0:
        self.text = '-'
    return self.active


#================================================================[ Render Loop ]

def drawcall(i):
  glutPostRedisplay()
  glutTimerFunc(0,drawcall,1)

def display():
  # reset
  glClear( GL_COLOR_BUFFER_BIT )
  glBindTexture( GL_TEXTURE_2D, 0 )
  glColor( 1.0, 1.0, 1.0, 1.0 )
  # background
  glBindTexture( GL_TEXTURE_2D, ctrl.tex_lib.background )
  glBegin( GL_QUADS )
  glTexCoord2f( 0.0, 0.0 )
  glVertex2i( 0, 0 )
  glTexCoord2f( 1.0, 0.0 )
  glVertex2i( 1000, 0 )
  glTexCoord2f( 1.0, 1.0 )
  glVertex2i( 1000, 550 )
  glTexCoord2f( 0.0, 1.0 )
  glVertex2i( 0, 550 )
  glEnd()
  # current parameter set
  if   ctrl.act_param == 'box':    glBindTexture( GL_TEXTURE_2D, ctrl.tex_lib.param_box );    posdim = (60,280,83,143)
  elif ctrl.act_param == 'star':   glBindTexture( GL_TEXTURE_2D, ctrl.tex_lib.param_star );   posdim = (60,225,144,195)
  elif ctrl.act_param == 't':      glBindTexture( GL_TEXTURE_2D, ctrl.tex_lib.param_T );      posdim = (60,180,152,241)
  elif ctrl.act_param == 'circle': glBindTexture( GL_TEXTURE_2D, ctrl.tex_lib.param_circle ); posdim = (60,285,108,135)
  elif ctrl.act_param == 'custom': glBindTexture( GL_TEXTURE_2D, ctrl.tex_lib.param_custom ); posdim = (60,390,123,34)
  glBegin( GL_QUADS )
  glTexCoord2f( 0.0, 0.0 )
  glVertex2i( posdim[0], posdim[1] )
  glTexCoord2f( 1.0, 0.0 )
  glVertex2i( posdim[0]+posdim[2], posdim[1] )
  glTexCoord2f( 1.0, 1.0 )
  glVertex2i( posdim[0]+posdim[2], posdim[1]+posdim[3] )
  glTexCoord2f( 0.0, 1.0 )
  glVertex2i( posdim[0], posdim[1]+posdim[3] )
  glEnd()
  # default text fields
  for f in ctrl.txt_fields:
    f.display()
  # finish frame
  glutSwapBuffers()


#=============================================================[ Script Creation ]

def generateScript():
  try:
    if 'win' in sys.platform:
      script = open( 'RatLabScript.bat', 'w' )
    elif 'linux' in sys.platform:
      script = open( 'RatLabScript', 'w' )
  except:
    print('Error! Script file creation failed!')
    sys.exit()
  # get values
  if   ctrl.act_param == 'box':     env_param = 'dim '+ctrl.box_fields[0].text+' '+ctrl.box_fields[1].text+' '+ctrl.box_fields[2].text
  elif ctrl.act_param == 'star':    env_param = 'star_maze '+ctrl.star_fields[0].text+' '+ctrl.star_fields[1].text+' '+ctrl.star_fields[2].text+' '+ctrl.star_fields[3].text
  elif ctrl.act_param == 't':       env_param = 't_maze '+ctrl.t_fields[0].text+' '+ctrl.t_fields[1].text+' '+ctrl.t_fields[2].text+' '+ctrl.t_fields[3].text+' '+ctrl.t_fields[4].text
  elif ctrl.act_param == 'circle':  env_param = 'circle_maze '+ctrl.circle_fields[0].text+' '+ctrl.circle_fields[1].text+' '+ctrl.circle_fields[2].text
  elif ctrl.act_param == 'custom':  env_param = 'custom_maze '+ctrl.custom_fields[0].text
  frames    = 'record limit ' +ctrl.def_fields[0].text if ctrl.def_fields[0].text!='-' else ''
  batch     = 'batch_size '   + ctrl.def_fields[ 1].text if ctrl.def_fields[1].text != '-' else ''
  tr_frames = 'frames '       + ctrl.def_fields[ 2].text if ctrl.def_fields[2].text != '-' else ''
  ica       = 'ICA'          if ctrl.def_fields[ 3].tick else ''
  noise     = 'noise'        if ctrl.def_fields[ 4].tick else ''
  speed     = 'speed '        + ctrl.def_fields[ 5].text if ctrl.def_fields[5].text != '-' else ''
  mom       = 'mom '          + ctrl.def_fields[ 6].text if ctrl.def_fields[6].text != '-' else ''
  arc       = 'arc '          + ctrl.def_fields[ 7].text if ctrl.def_fields[7].text != '-' else ''
  small_fov = 'small_fov'    if ctrl.def_fields[ 8].tick else ''
  path_loop = 'loop'         if ctrl.def_fields[ 9].tick else ''
  path      = 'path '         + ctrl.def_fields[10].text if ctrl.def_fields[10].text != '-' else ''
  # write
  r = 'python ratlab.py color '+frames+' '+env_param+' '+speed+' '+mom+' '+arc+' '+small_fov+' '+path+' '+path_loop+'\n'
  c = 'python convert.py\n'
  t = 'python train.py '+batch+' '+tr_frames+' '+noise+' '+ica+'\n'
  s = 'python sample.py - 1 32 all\n'
  script.write(r)
  script.write(c)
  script.write(t)
  script.write(s)
  print('Executable RatLab script written to file \'RatLabScript\'')
  script.close()


#===================================================================[ Callback ]

def keyboardPress( key, x, y ):
  # ESC: quit program
  if ord(key) == 27:
    print('user abort')
    sys.exit()
  # text field input
  elif ctrl.act_field != None:
    if ord(key) == 8: # backspace
      ctrl.act_field.input(None)
    elif key in b'1234567890_.-\/abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ':
      ctrl.act_field.input(key.decode())   

def mouseClick( btn, state, x, y ):
  y = 550 - y
  if btn == 0 and state == 0:
    ctrl.act_field = None
    for f in ctrl.txt_fields:
      if f.select(x, y) == True:
        ctrl.act_field = f
        # default buttons 
        if f in ctrl.def_buttons:
          # generate script
          if f.tag == 'script':
            generateScript()
            return
          # select current parameter set
          for f2 in ctrl.def_buttons:
            if f2!=f: f2.act=False
          if f.tag == ctrl.act_param: continue
          elif f.tag == 'box':
            ctrl.act_param  = 'box'
            ctrl.txt_fields = [] + ctrl.def_buttons + ctrl.def_fields + ctrl.box_fields
          elif f.tag == 'star':
            ctrl.act_param = 'star'
            ctrl.txt_fields = [] + ctrl.def_buttons + ctrl.def_fields + ctrl.star_fields
          elif f.tag == 't':
            ctrl.act_param = 't'
            ctrl.txt_fields = [] + ctrl.def_buttons + ctrl.def_fields + ctrl.t_fields
          elif f.tag == 'circle':
            ctrl.act_param = 'circle'
            ctrl.txt_fields = [] + ctrl.def_buttons + ctrl.def_fields + ctrl.circle_fields
          elif f.tag == 'custom':
            ctrl.act_param = 'custom'
            ctrl.txt_fields = [] + ctrl.def_buttons + ctrl.def_fields + ctrl.custom_fields


#=====================================================================[ OpenGL ]

def setupOpenGL():
  # GLUT window
  glutInit( sys.argv )
  glutInitDisplayMode( GLUT_DOUBLE | GLUT_RGBA | GLUT_DEPTH )
  glutInitWindowSize( 1000, 550 )
  glutCreateWindow( b'RatLabGUI' )
  # GLUT display
  glutDisplayFunc( display )
  glutTimerFunc( 0, drawcall, 1 )
  # GLUT callback
  glutKeyboardFunc( keyboardPress )
  glutMouseFunc( mouseClick )
  # OpenGL projection matrix setup for 2D drawing plane
  glViewport( 0, 0, 1000, 550 )
  glMatrixMode(GL_PROJECTION)
  glLoadIdentity()
  gluOrtho2D(0, 1000, 0, 550 )
  glMatrixMode( GL_MODELVIEW )
  glLoadIdentity()
  # misellaneous parameters
  glClearColor( 0.0, 0.0, 0.0, 1.0 )
  # texture mapping
  glEnable( GL_TEXTURE_2D )
  # blending
  glEnable(GL_BLEND)
  glBlendFunc (GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

#=======================================================================[ Main ]

def main():
  setupOpenGL()
  global ctrl 
  ctrl = Ctrl()
  glutMainLoop()

main() # <<<   <<<   <<<   <<<   <<<   <<<   <<<   <<<   <<<   <<<   <<<[ main ]
