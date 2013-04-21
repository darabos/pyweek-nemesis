# For py2app/py2exe use.

import os
import sys
if sys.version.startswith('2.7') and sys.platform == 'darwin':
  import pygame._view
elif sys.version.startswith('2.6') and sys.platform == 'darwin':
  import ctypes.util
elif sys.platform == 'win32':
  import OpenGL.platform.win32
  import OpenGL.arrays.ctypesarrays
  import OpenGL.arrays.lists
  import OpenGL.arrays.numbers
  import OpenGL.arrays.strings
  import OpenGL.arrays.nones
  import OpenGL_accelerate.formathandler

# Start the game.
import run_game
run_game.Start()
