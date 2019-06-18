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

## SETTINGS AND KEYBINDER ##


import os.path as ospath

import json

from bge import logic, events, render

from mathutils import Vector, Matrix

from game3 import keymap, config


def SaveJSON(name, dict, pretty=None):
	file = open(name, "w")

	json.dump(dict, file, indent="  ")

	file.close()


def LoadJSON(name):
	try:
		file = open(name, "r")
	except OSError:
		return None

	dict = json.load(file)

	file.close()
	return dict


def SaveBinds():
	path = logic.globalDict["DATA"]["GAMEPATH"]
	profile = logic.globalDict["CURRENT"]["Profile"]
	if "_" in profile:
		profile = "Base"

	binds = keymap.BINDS
	dict = {}

	for key in binds:
		if getattr(binds[key], "getData", None) != None:
			dict[key] = binds[key].getData()

	dict["MOUSELOOK"] = keymap.MOUSELOOK.getData()
	dict["CALIBRATE"] = {}
	for AXIS in events.AXISCALIBRATION:
		dict["CALIBRATE"][str(int(AXIS))] = events.AXISCALIBRATION[AXIS]

	name = path+profile+"Keymap.json"

	SaveJSON(name, dict)

	print("NOTICE: Keybinds Saved...\n\t", name)


def LoadBinds():
	path = logic.globalDict["DATA"]["GAMEPATH"]
	profile = logic.globalDict["CURRENT"]["Profile"]
	if "_" in profile:
		profile = "Base"

	name = path+profile+"Keymap.json"

	binds = keymap.BINDS
	dict = LoadJSON(name)

	## SET EXIT KEY ##
	if config.EMBEDDED_FIX == False:
		logic.setExitKey(keymap.events.PAUSEKEY)
		print("Exit Key Changed: [events.PAUSEKEY]")

	## ASSIGN KEYMAP ##
	if dict == None:
		print("ERROR: File not Found...\n\t", name)
		return

	for key in binds:
		if getattr(binds[key], "setData", None) != None and key in dict:
			binds[key].setData(dict[key])

	if "MOUSELOOK" in dict:
		keymap.MOUSELOOK.setData(dict["MOUSELOOK"])

	if "CALIBRATE" in dict:
		for AXIS in dict["CALIBRATE"]:
			events.AXISCALIBRATION[int(AXIS)] = dict["CALIBRATE"][AXIS]

	print("NOTICE: Keybinds Loaded...\n\t", name)


def checkWorldData(path, launcher=False):
	path = path+"\\"
	print(path)

	if config.UPBGE_FIX == True:
		dict = LoadJSON(path+"gd_dump")
		if dict != None:
			if dict["TRAVELING"] == True:
				logic.globalDict = dict
				logic.globalDict["TRAVELING"] = False
				SaveJSON(logic.globalDict["DATA"]["GAMEPATH"]+"gd_dump", {"TRAVELING":False}, "\t")

	if "CURRENT" not in logic.globalDict:
		GenerateGlobalDict(path)
	return True


def GenerateGlobalDict(path):
	logic.globalDict = {"PROFILES": {}}

	logic.globalDict["PROFILES"]["__guest__"] = GenerateProfileData()

	logic.globalDict["BLENDS"] = logic.getBlendFileList(path+"MAPS")
	logic.globalDict["DATA"] = {"GAMEPATH":path, "PROFILES":[]}
	logic.globalDict["GRAPHICS"] = GenerateGraphicsData()
	logic.globalDict["CURRENT"] = {"Profile":"__guest__", "Level":None, "Scene":None}

	logic.globalDict["TRAVELING"] = False
	logic.globalDict["SCREENSHOT"] = {"Trigger":False, "Count":None}

def GenerateProfileData():
	return {"LVLData":{}, "PLRData":{}, "GLBData":{}, "Portal":{}, "Settings":{}}

def GenerateLevelData():
	return {"SPAWN":[], "DROP":[], "CLIP":config.LOW_CLIP}

def GenerateGraphicsData():
	save = False
	file = logic.globalDict["DATA"]["GAMEPATH"]+"Graphics.cfg"
	data = LoadJSON(file)

	if data == None:
		print("NOTICE: No Graphics Config...")
		save = True
		data = {}

	dict = {
		"Shaders": data.get("Shaders", "HIGH"),
		"Vsync": data.get("Vsync", True),
		"Fullscreen": data.get("Fullscreen", True),
		"Resolution": data.get("Resolution", None),
		"Debug": data.get("Debug", [True, True, True, True])
	}

	if config.EMBEDDED_FIX == False:
		render.setFullScreen(dict["Fullscreen"])

	X = render.getWindowWidth()
	Y = render.getWindowHeight()

	if dict["Resolution"] == None:
		print("NOTICE: Initializing Resolution...")
		dict["Resolution"] = [X, Y]
	if dict["Resolution"][0] > X or dict["Resolution"][1] > Y or len(dict["Resolution"]) >= 3:
		print("WARNING: Resolution out of Range...")
		dict["Resolution"] = [X, Y]

	if config.EMBEDDED_FIX == False:
		if dict["Resolution"][0] % 2 != 0:
			dict["Resolution"][0] -= 1
			print("NOTICE: Resolution Fix")
		if dict["Resolution"][1] % 2 != 0:
			dict["Resolution"][1] -= 1
			print("NOTICE: Resolution Fix")

		render.setWindowSize(dict["Resolution"][0], dict["Resolution"][1])
		if save == True:
			SaveJSON(file, dict)

	elif len(dict["Resolution"]) <= 2:
		dict["Resolution"].append("EMBEDDED")

	print("...")

	return dict


def applyGraphics():
	graphics = logic.globalDict["GRAPHICS"]

	if config.EMBEDDED_FIX == True:
		return

	if SCREENSHOT not in logic.getSceneList()[0].post_draw:
		logic.getSceneList()[0].post_draw.append(SCREENSHOT)

	## RESOLUTION ##
	X = render.getWindowWidth()
	Y = render.getWindowHeight()

	print("GRAPHICS:\n\tResolution", X, Y)

	## DEBUG ##
	debug = graphics["Debug"]
	render.showFramerate(debug[1] and debug[0])
	render.showProfile(debug[2] and debug[0])
	render.showProperties(debug[3] and debug[0])

	## VSYNC ##
	if graphics["Vsync"] == True:
		#render.setVsync(render.VSYNC_ON)
		print("\tVsync ON")
	elif graphics["Vsync"] == False:
		#render.setVsync(render.VSYNC_OFF)
		print("\tVsync OFF")

	## SHADERS ##
	glsl = ["lights", "shaders", "shadows", "ramps", "extra_textures"]

	for setting in glsl:
		render.setGLSLMaterialSetting(setting, True)

	if graphics["Shaders"] == "LOW":
		for setting in glsl:
			render.setGLSLMaterialSetting(setting, False)
		render.setAnisotropicFiltering(1)
		print("\tShaders LOW\n\tAnisotrpic OFF\n\tMipmap NEAR")

	elif graphics["Shaders"] == "MEDIUM":
		for setting in glsl:
			if setting == "shaders":
				render.setGLSLMaterialSetting(setting, False)
			else:
				render.setGLSLMaterialSetting(setting, True)
		render.setAnisotropicFiltering(4)
		print("\tShaders MED\n\tAnisotrpic x4\n\tMipmap NEAR")

	elif graphics["Shaders"] == "HIGH":
		for setting in glsl:
			render.setGLSLMaterialSetting(setting, True)
		render.setAnisotropicFiltering(16)
		render.setMipmapping(2)
		print("\tShaders HIGH\n\tAnisotrpic x16\n\tMipmap FAR")


def SCREENSHOT():
	screen = logic.globalDict["SCREENSHOT"]

	path = ospath.normpath(logic.globalDict["DATA"]["GAMEPATH"]+config.SCREENSHOT_PATH)+"\\"

	curlvl = str(logic.globalDict["CURRENT"]["Level"]).replace(".blend", "")

	if screen["Count"] == None:
		dict = LoadJSON(path+"marker.json")
		if dict == None:
			num = 0
		else:
			num = dict["Value"]
		screen["Count"] = num

	if screen["Trigger"] == "Launcher":
		curlvl = "Launcher"
		screen["Trigger"] = True

	if screen["Trigger"] == True:
		num = str(screen["Count"])
		if screen["Count"] > 999:
			count = num
		else:
			list = ["0"]*(3-len(num))
			list.append(num)
			count = "".join( list )

		name = path+curlvl+"\\screen"+count+".png"
		render.makeScreenshot(name)

		screen["Count"] += 1
		screen["Trigger"] = False
		SaveJSON(path+"marker.json", {"Value":screen["Count"]})
		print("FREEZE FRAME!")
		print("\t", name)




