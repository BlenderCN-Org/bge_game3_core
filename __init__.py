####
# bge_game3_core: Full python game structure for the Blender Game Engine
# Copyright (C) 2019  DaedalusMDW @github.com (Daedalus_MDW @blenderartists.org)
# https://github.com/DaedalusMDW/bge_game3_core
#
# This file is part of bge_game3_core.
#
#    bge_game3_core is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    bge_game3_core is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with bge_game3_core.  If not, see <http://www.gnu.org/licenses/>.
#
####


import sys
import os.path as ospath

print(__file__)
GAMEPATH = ospath.normpath(__file__+"\\..\\..\\")
sys.path.append(GAMEPATH)

for i in sys.path:
	print("PATH:", i)

COREBLENDS = {
	"ASSETS": ospath.normpath(__file__+"\\..\\CoreAssets.blend"),
	"HUD": ospath.normpath(__file__+"\\..\\CoreOverlay.blend")
}


## CHECK VERSION ##
from . import config

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
from . import settings

settings.checkWorldData(GAMEPATH)
settings.applyGraphics()
settings.LoadBinds()


print("\n\t...game3 core init...\n")


from bge import logic

logic.UPDATELIST = []
logic.PLAYERLIST = []
logic.PLAYERLIST = []
logic.HUDCLASS = None
logic.VIEWPORT = None

del logic
