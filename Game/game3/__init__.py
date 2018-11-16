

import sys
import os.path as ospath

print(__file__)
GAMEPATH = ospath.normpath(__file__+"\\..\\..\\")
sys.path.append(GAMEPATH)

for i in sys.path:
	print("PATH:", i)

try:
	import bpy
	logic.endGame()
	raise RuntimeError("Embedded Player Dectected...")
except ImportError:
	pass

from . import settings, config

try:
	from bge import app

	config.UPBGE_FIX = True
	config.MOUSE_FIX = False
	if app.upbge_version[1] >= 2 and app.upbge_version[2] >= 2:
		config.MOUSE_FIX = True
	del app

except Exception:
	config.UPBGE_FIX = False
	config.MOUSE_FIX = False

print("\n\t...game3 core init...\n")

settings.checkWorldData(GAMEPATH)
settings.applyGraphics()

from bge import logic
logic.UPDATELIST = []
logic.PLAYERCLASS = None
logic.HUDCLASS = None

