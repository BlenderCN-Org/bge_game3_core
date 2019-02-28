

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
	config.ASYNC_FIX = False
	print("UPBGE", app.upbge_version)
	if app.upbge_version[1] >= 2:
		if app.upbge_version[2] >= 2:
			config.MOUSE_FIX = True
		if app.upbge_version[2] >= 4:
			config.ASYNC_FIX = True
	del app

except Exception:
	config.UPBGE_FIX = False
	config.MOUSE_FIX = False
	config.ASYNC_FIX = False


## NO VIEWPORT PLAYER ##
try:
	import bpy
	config.EMBEDDED_FIX = True
	print("NOTICE: Embedded Player Dectected...")
except ImportError:
	config.EMBEDDED_FIX = False


## SETUP DATA ##
settings.checkWorldData(GAMEPATH)
settings.applyGraphics()

settings.LoadBinds()

print("\n\t...game3 core init...\n")

libblend = ospath.normpath(__file__+"\\..\\CoreAssets.blend")
logic.LibLoad(libblend, "Scene", load_actions=True, verbose=False, load_scripts=True)
del libblend

logic.UPDATELIST = []
logic.PLAYERCLASS = None
logic.HUDCLASS = None
logic.VIEWPORT = None

