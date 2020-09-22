#==============================================================================
#
#  Copyright (C) 2016 Fabian Schoenfeld
#
#  This file is part of the hippolab software. It is free software; you can
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


# prohibit Python from adding class members during runtime
class Freezeable( object ):

    def freeze( self ):
        self._frozen = None

    def __setattr__( self, name, value ):
        if hasattr( self, '_frozen' )and not hasattr( self, name ):
            raise AttributeError( "Error! No adding additional attribute '%s' to class '%s'!" % (name,self.__class__.__name__) )
        object.__setattr__( self, name, value )
