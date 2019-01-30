

import sys
import os.path as ospath

print(__file__)
GAMEPATH = ospath.normpath(__file__+"\\..\\..\\")
sys.path.append(GAMEPATH)

for i in sys.path:
	print("PATH:", i)

from bge import logic


## CHECK VERSION ##
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


## NO VIEWPORT PLAYER ##
try:
	import bpy
	logic.endGame()
	raise RuntimeError("Embedded Player Dectected...")
except ImportError:
	pass


## SETUP DATA ##
settings.checkWorldData(GAMEPATH)
settings.applyGraphics()

settings.LoadBinds()

print("\n\t...game3 core init...\n")


logic.UPDATELIST = []
logic.PLAYERCLASS = None
logic.VIEWPORT = None
logic.HUDCLASS = None

