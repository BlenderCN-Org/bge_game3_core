####
# bge_game-3.0_template: Full python game structure for the Blender Game Engine
# Copyright (C) 2018  DaedalusMDW @github.com (Daedalus_MDW @blenderartists.org)
#
# This file is part of bge_game-3.0_template.
#
#    bge_game-3.0_template is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    bge_game-3.0_template is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with bge_game-3.0_template.  If not, see <http://www.gnu.org/licenses/>.
#
####

## LAUNCHER ##

import sys
for i in sys.path:
	print("PATH:", i)

from bge import logic, render

import PYTHON.settings as settings
import PYTHON.keymap as keymap


if "PROFILES" not in logic.globalDict:
	logic.globalDict = {"PROFILES": {}}

	logic.globalDict["PROFILES"]["__guest__"] = settings.GenerateProfileData()

if "CURRENT" not in logic.globalDict:
	logic.globalDict["BLENDS"] = logic.getBlendFileList("//MAPS")
	logic.globalDict["DATA"] = {"GAMEPATH":logic.expandPath("//"), "Portal":{"Door":None, "Vehicle":None, "Zone":None, "Scene":None}}
	logic.globalDict["CURRENT"] = {"Profile":"__guest__", "Level":None, "Player":None, "Scene":None}
	logic.globalDict["GRAPHICS"] = settings.GenerateGraphicsData("LOW" in logic.getCurrentController().owner)

settings.SETGFX(logic.globalDict["GRAPHICS"], launcher=True)


def RUN(cont):

	OWNER = cont.owner

	OWNER["Class"].RUN()
	OWNER["Class"].STATS()


class LAUNCHER:

	"""Syntax: (one space only, hypens only)
		> command -x -y

	Profile Commands:
		login:        open a profile
		save:         saves active profile
		load:         load profile data from file

	Utilities:
		keymap:       open the keymap editor

	Game Commands:
		open:         open a blend file
		resume:       continue game
		player:       switch the active character
		exit:         close the game without saving

	Graphics Settings:
		quality:      set shader level (big performace boost)
		resolution:   change the resolution/window size
		vsync:        toggle vsync
		debug:        toggle debug properties; cfg file [master, fps, stats, properties]"""

	VERSION = "0.4.4"
	OFFSET = 1

	def __init__(self, OWNER):
		self.scene = logic.getCurrentScene()
		self.owner = OWNER
		self.owner.text = ""
		self.handle = " > "
		self.line = []
		self.index = 0
		self.prompt = None
		self.que = None
		self.history = {"ID":0, "LIST":[None]}
		self.loading = False
		self.statdict = {}

		self.STATS()
		self.NEWLINE("Type 'help' for list of commands.  Use '-?' argument for info about a command.", 2, 1, (0.7,0.5,0.7,1))
		#self.NEWLINE("WARNING: State System Being Revised, Expect Oddities...", 2, 1, (1.0,0.5,0.0,1))

	def STATS(self):
		gfx = logic.globalDict["GRAPHICS"]
		self.STATSLINE("Version", self.VERSION)
		self.STATSLINE("Resolution", str(gfx["Resolution"][0])+"x"+str(gfx["Resolution"][1]) )
		self.STATSLINE("Shaders", gfx["Shaders"])

		for key in ["Profile", "Player", "Level"]:
			self.STATSLINE(key, str(logic.globalDict["CURRENT"][key]))

		if logic.globalDict["DATA"]["Portal"]["Vehicle"] != None:
			vehtext = logic.globalDict["DATA"]["Portal"]["Vehicle"]["Object"]
			self.statdict["Player"][1]["SUB"] = vehtext

	def STATSLINE(self, keytext, valtext):
		OBJ = self.scene.objects["Stats"]
		col_key = (0.7, 0.7, 0.7, 1)
		col_val = (1.0, 1.0, 1.0, 1)

		if keytext in self.statdict:
			key = self.statdict[keytext][0]
			val = self.statdict[keytext][1]
		else:
			key = self.scene.addObject("Text", OBJ, 0)
			val = self.scene.addObject("Text", OBJ, 0)
			key.setParent(self.scene.active_camera)
			val.setParent(self.scene.active_camera)
			self.statdict[keytext] = [key, val]
			OBJ.worldPosition[1] -= 1

		key.text = keytext+":"
		key.color = col_key

		if valtext == None or "__" in valtext:
			valtext = "None"
		if ".blend" in valtext:
			valtext = valtext.split(".blend")[0]
		if "SUB" in val:
			valtext = valtext+" <"+val["SUB"]+">"
		val.text = "{:>32}".format(valtext)
		val.color = col_val

	def RUN(self):
		SCENE = self.scene
		OWNER = self.owner
		CAM = SCENE.active_camera
		KBE = logic.keyboard.events

		for input in KBE:
			if KBE[input] == 1:
				if input in [keymap.events.ENTERKEY, keymap.events.PADENTER]:
					if self.prompt != None:
						self.APPLY()
					elif len(self.line) > 1:
						self.EXECUTE()

					clip = (CAM.worldPosition[1] - OWNER.worldPosition[1])
					if clip > 14:
						CAM.worldPosition[1] = OWNER.worldPosition[1]+14

				elif input == keymap.events.ESCKEY:
					if self.prompt != None:
						self.CANCEL()

				elif input == keymap.events.LEFTARROWKEY:
					if self.index > 0:
						self.index -= 1

				elif input == keymap.events.RIGHTARROWKEY:
					if self.index < len(self.line):
						self.index += 1

				elif input == keymap.events.UPARROWKEY:
					line = self.history["LIST"][self.history["ID"]]
					if line != None:
						self.line = line.copy()
						self.index = len(self.line)
					if self.history["ID"] < len(self.history["LIST"])-1:
						self.history["ID"] += 1

				elif input == keymap.events.DOWNARROWKEY:
					line = self.history["LIST"][self.history["ID"]]
					if line != None:
						self.line = line.copy()
						self.index = len(self.line)
					if self.history["ID"] > 0:
						self.history["ID"] -= 1

				elif input == keymap.events.TABKEY:
					self.line.insert(self.index, "    ")
					self.index += 1

				elif input != keymap.events.BACKSPACEKEY:
					shift = keymap.SYSTEM["SHIFT"].checkModifiers()
					char = keymap.events.EventToCharacter(input, shift)
					if char == " ":
						if self.index < 1:
							return
						elif self.line[self.index-1] == " ":
							return
					if char not in ["", "_"]:
						self.line.insert(self.index, char)
						self.index += 1

				elif len(self.line) > 0 and self.index > 0:
					self.line.pop(self.index-1)
					self.index -=1

		line = self.line.copy()
		line.insert(self.index, "_")

		text = "".join(line)
		prf = logic.globalDict["CURRENT"]["Profile"]
		if self.que != None or "_" in prf:
			prf = ""

		OWNER.text = prf+self.handle+text

		if CAM.worldPosition[1] > OWNER.worldPosition[1]:
			if keymap.SYSTEM["WHEEL_DOWN"].tap() == True:
				CAM.worldPosition[1] -= 1
		if CAM.worldPosition[1] < 0:
			if keymap.SYSTEM["WHEEL_UP"].tap() == True:
				CAM.worldPosition[1] += 1

		OWNER["index"] = self.index
		OWNER["scroll"] = int(-CAM.worldPosition[1])

		if keymap.SYSTEM["SCREENSHOT"].tap() == True:
			settings.triggerPrintScreen("Launcher")

	def EXECUTE(self):
		self.history["ID"] = 0
		self.history["LIST"].insert(0, self.line.copy())

		text = "".join(self.line)

		self.NEWLINE(self.handle+text, 2)

		split = text.split(" -")
		split[0] = split[0].upper()

		CMD = globals().get(split[0], "Fail")

		if CMD == "Fail":
			CMD = ERROR

		if "?" in split[0] or split[0] in ["HELP", "DOCS", "INFO", "COMMANDS"]:
			self.DOCSLINE(self.__doc__)
		elif "?" in split:
			self.DOCSLINE(CMD.__doc__)
		else:
			CMD(split)

	def APPLY(self):

		text = "".join(self.line)

		CHECK = self.prompt(args=[], kwa=text)
		if CHECK == False:
			return

		self.que.pop(0)

		self.NEWLINE(self.handle+text, 2)
		if CHECK == "LOAD":
			logic.CLASS.NEWLINE("LOADING...", 2, 0, (1,1,1,1))
		elif CHECK != True:
			logic.CLASS.NEWLINE("ERROR: "+str(CHECK), 2, 0, (0.3,0.5,0.7,1))

		if len(self.que) == 0:
			self.CANCEL()
		else:
			self.handle = self.que[0]+":"

	def CANCEL(self):
		self.que = None
		self.prompt = None
		self.handle = " > "
		self.owner.worldPosition[0] = 0

	def NEWLINE(self, text=None, lines=1, tab=0, color=(0.5, 0.5, 0.5, 1)):
		if text != None:
			last = self.scene.addObject("Text", self.owner, 0)
			last.text = text
			last.color = color
			last.worldPosition[0] += tab*2

		self.line = []
		self.index = 0

		self.owner.worldPosition[1] -= (self.OFFSET*lines)

	def DOCSLINE(self, docs):
		list = docs.split("\n")
		for i in range(len(list)):
			text = list[i]
			tab = 1
			for char in text:
				if char == "	":
					tab += 1
			if tab > 1:
				tab -= 1
			text = text.replace("	", "")
			self.NEWLINE(text, 1, tab, (0.7,0.5,0.7,1))
		self.NEWLINE()

	def ENTRYLINE(self, que):
		self.handle = que[0]+":"
		self.owner.worldPosition[0] = 4
		self.que = que


OWNER = logic.getCurrentController().owner
logic.CLASS = LAUNCHER(OWNER)
OWNER["Class"] = logic.CLASS


## Command Functions ##

def ERROR(args=[]):
	logic.CLASS.NEWLINE("ERROR:", 1, 1, (0.3,0.5,0.7,1))
	logic.CLASS.NEWLINE("Not Vaild Command...", 2, 2, (1,1,1,1))


def EXIT(args=[], kwa=None):
	"""Exit the Command Console"""

	logic.endGame()


def RESUME(args=[], kwa=None):
	"""Resume from Last Save"""

	current = logic.globalDict["CURRENT"]
	profile = logic.globalDict["PROFILES"][current["Profile"]]

	map = current["Level"]

	if map == None or map not in logic.globalDict["BLENDS"]:
		logic.CLASS.NEWLINE("ERROR:", 1, 1, (0.3,0.5,0.7,1))
		logic.CLASS.NEWLINE("Map Not Available...", 2, 2, (1,1,1,1))
		return

	#if map not in profile["LVLData"]:
	#	logic.CLASS.NEWLINE("ERROR:", 1, 1, (0.3,0.5,0.7,1))
	#	logic.CLASS.NEWLINE("Something Happened...", 2, 2, (1,1,1,1))
	#	return

	logic.startGame(logic.expandPath("//MAPS/"+map))
	logic.CLASS.NEWLINE("LOADING...", 2, 2, (1,1,1,1))


def KEYMAP(args=[], kwa=None):
	"""Open Keymap Utility"""

	logic.startGame(logic.expandPath("//")+"Keymap.blend")


def MOUSE(args=[], kwa=None):
	""" Mouse Settings

	-s              Set Speed (1 - 100)
	-i              Set Smoothing (0 Disables)"""

	current = logic.globalDict["CURRENT"]
	profile = logic.globalDict["PROFILES"][current["Profile"]]

	#if len(args) > 1:
	#	split = args[1].split(" ")
	#	if split[0] == "s":
	#		profile["Settings"]


def VSYNC(args=[], kwa=None):
	"""Switch Vsync On/Off"""

	if logic.globalDict["GRAPHICS"]["Vsync"] == False:
		logic.globalDict["GRAPHICS"]["Vsync"] = True
	else:
		logic.globalDict["GRAPHICS"]["Vsync"] = False

	logic.CLASS.NEWLINE("Vsync: "+str(logic.globalDict["GRAPHICS"]["Vsync"]), 2, 2, (1,1,1,1))

	settings.SETGFX(launcher=True, save=True)


def DEBUG(args=[], kwa=None):
	"""Switch Debug On/Off"""

	debug = logic.globalDict["GRAPHICS"]["Debug"]

	if debug[0] == False:
		logic.globalDict["GRAPHICS"]["Debug"][0] = True
		logic.CLASS.NEWLINE("Debug Stats ON", 2, 2, (1,1,1,1))
	else:
		logic.globalDict["GRAPHICS"]["Debug"][0] = False
		logic.CLASS.NEWLINE("Debug Stats OFF", 2, 2, (1,1,1,1))

	render.showFramerate(debug[1] and debug[0])
	render.showProfile(False)
	render.showProperties(debug[3] and debug[0])

	settings.SETGFX(launcher=True, save=True)


def RESOLUTION(args=[], kwa=None):
	"""Set Render Resolution

	-x              Window Width
	-y              Window Height
	-f              Fullscreen Toggle
	-l              Set Recommended Low (1280x720)
	-m              Set Recommended Medium (1600x900)
	-h              Set Recommended High (1920x1080)"""

	if "f" in args:
		logic.globalDict["GRAPHICS"]["Fullscreen"] ^= True
		fs = logic.globalDict["GRAPHICS"]["Fullscreen"]
		#X, Y = logic.globalDict["GRAPHICS"]["Resolution"]
		#render.setFullScreen(fs)
		#render.setWindowSize(X, Y)
		logic.CLASS.NEWLINE("Fullscreen: "+str(fs)+" (Relaunch Required)", 2, 2, (1,1,1,1))
		#settings.SETGFX(launcher=True, save=True)
		#return

	X = None
	Y = None

	if "l" in args:
		X = 1280
		Y = 720

	elif "m" in args:
		X = 1600
		Y = 900

	elif "h" in args:
		X = 1920
		Y = 1080

	elif len(args) > 1:
		for i in args:
			if "x " in i:
				X = int(i.split(" ")[1])
				if X % 2 != 0:
					X -= 1
			if "y " in i:
				Y = int(i.split(" ")[1])
				if Y % 2 != 0:
					Y -= 1

	else:
		X = render.getWindowWidth()
		Y = render.getWindowHeight()

		logic.CLASS.NEWLINE("Resolution: "+str(X)+"x"+str(Y), 2, 2, (1,1,1,1))
		return

	if X != None and Y != None:
		render.setWindowSize(X, Y)

	X = render.getWindowWidth()
	Y = render.getWindowHeight()

	logic.globalDict["GRAPHICS"]["Resolution"] = [X,Y]
	logic.CLASS.NEWLINE("Resolution: "+str(X)+"x"+str(Y), 2, 2, (1,1,1,1))

	settings.SETGFX(launcher=True, save=True)


def QUALITY(args=[], kwa=None):
	"""Set the Graphics Quality

	-l              Disable Lights and Shaders
	-m              Disable Specular Lighting and Anisotropic Filtering
	-h              Full Shading with Anisotropic x16"""

	if len(args) == 1:
		setting = logic.globalDict["GRAPHICS"]["Shaders"]
		logic.CLASS.NEWLINE("Quality: "+setting, 2, 2, (1,1,1,1))
		return

	if args[1] == "l":
		setting = "LOW"
	elif args[1] == "m":
		setting = "MEDIUM"
	elif args[1] == "h":
		setting = "HIGH"
	else:
		setting = None

	if setting in ["LOW", "MEDIUM", "HIGH"]:
		logic.globalDict["GRAPHICS"]["Shaders"] = setting
		logic.CLASS.NEWLINE("Quality: "+setting, 2, 2, (1,1,1,1))

		settings.SETGFX(launcher=True, save=True)


def SAVE(args=[], kwa=None):
	"""Save Current Profile"""

	current = logic.globalDict["CURRENT"]
	profile = logic.globalDict["PROFILES"][current["Profile"]]
	portal = logic.globalDict["DATA"]["Portal"]

	path = logic.globalDict["DATA"]["GAMEPATH"]
	name = "Base"

	if "_" not in current["Profile"]:
		name = current["Profile"]

	profile["Last"]["CURRENT"] = current.copy()
	profile["Last"]["PORTAL"] = portal.copy()
	dict = profile

	if "Switch" in args and len(args) == 1:
		return

	settings.SaveJSON(path+name+"Profile.sav", dict, "\t")
	logic.CLASS.NEWLINE("Profile Saved!", 2, 2, (1,1,1,1))

	settings.SETGFX(launcher=True, save=True)


def LOAD(args=[], kwa=None):
	"""Load Profile Data"""

	current = logic.globalDict["CURRENT"]

	path = logic.globalDict["DATA"]["GAMEPATH"]
	name = "Base"

	if "_" not in current["Profile"]:
		name = current["Profile"]

	dict = settings.LoadJSON(path+name+"Profile.sav")

	if dict == None:
		if "Return" in args and len(args) == 1:
			return None
		elif "Switch" in args and len(args) == 1:
			dict = logic.globalDict["PROFILES"][current["Profile"]]
		else:
			ERROR()
			return

	logic.globalDict["CURRENT"] = dict["Last"]["CURRENT"].copy()
	logic.globalDict["PROFILES"][current["Profile"]] = dict
	logic.globalDict["DATA"]["Portal"] = dict["Last"]["PORTAL"].copy()

	if "Return" in args and len(args) == 1:
		return dict

	logic.CLASS.NEWLINE("Profile Loaded!", 2, 2, (1,1,1,1))


def LOGIN(args=[], kwa=None):

	"""Login to a Profile, Creating New if Needed"""

	if kwa != None:
		if logic.CLASS.que[0] == "PROFILE":
			if len(kwa) < 2:
				return False
			kwa = kwa.capitalize()

			if kwa in ["None", "Guest", "Base"]:
				SAVE(["Switch"])
				logic.globalDict["CURRENT"]["Profile"] = "__guest__"
				LOAD(["Switch"])
				return "Guest Profile Loaded..."

			elif kwa in logic.globalDict["PROFILES"]:
				SAVE(["Switch"])
				logic.globalDict["CURRENT"]["Profile"] = kwa
				LOAD(["Switch"])
				return True

			else:
				SAVE(["Switch"])
				logic.globalDict["CURRENT"]["Profile"] = kwa
				dict = LOAD(["Return"])
				chk = True
				if dict == None:
					dict = settings.GenerateProfileData()
					chk = "Data Failed to Load, Creating New..."
					logic.globalDict["PROFILES"][kwa] = dict
					for key in logic.globalDict["DATA"]["Portal"]:
						logic.globalDict["DATA"]["Portal"][key] = None
					for key in logic.globalDict["CURRENT"]:
						if key != "Profile":
							logic.globalDict["CURRENT"][key] = None
				return chk

		return False

	if len(args) == 1:
		logic.CLASS.NEWLINE("Profile Names are Not Case Sensitive...", 2, 1, (0.7,0.5,0.7,1))
		logic.CLASS.ENTRYLINE(["PROFILE"])
		logic.CLASS.prompt = LOGIN

	if "list" in args:
		for p in logic.globalDict["PROFILES"]:
			if "_" not in p:
				if p == logic.globalDict["CURRENT"]["Profile"]:
					logic.CLASS.NEWLINE(p+" (Active)", 1, 1, (0.3,0.5,0.7,1))
				else:
					logic.CLASS.NEWLINE(p, 1, 1, (1,1,1,1))


def PLAYER(args=[], kwa=None):

	"""Change Player Class"""

	PL = ["Actor", "Red", "Blue", "Purple"]

	if kwa != None:
		if logic.CLASS.que[0] == "CLASS":
			if kwa in PL:
				logic.globalDict["CURRENT"]["Player"] = kwa
				return True
			try:
				if int(kwa) in range(len(PL)):
					logic.globalDict["CURRENT"]["Player"] = PL[int(kwa)]
					return True
			except Exception:
				return False

			if kwa == "None":
				logic.globalDict["CURRENT"]["Player"] = None
				return True
		return False

	if len(args) == 1:
		for i in range(len(PL)):
			logic.CLASS.NEWLINE(str(i)+": "+PL[i], 1, 1, (1,1,1,1))
		logic.CLASS.NEWLINE()
		logic.CLASS.NEWLINE("Enter Name or Index...", 2, 1, (0.7,0.5,0.7,1))

		logic.CLASS.ENTRYLINE(["CLASS"])
		logic.CLASS.prompt = PLAYER


def OPEN(args=[], kwa=None):

	"""Open a Map

	-list           Print blend files in "//MAPS/"
	-map <x>        Directly open "x.blend" or blendlist[x] if integer"""

	def checkNumber(x):
		try:
			int(x)
			return True
		except Exception:
			return False

	if kwa != None:
		map = kwa

		if ".blend" not in kwa:
			map = kwa+".blend"

		if checkNumber(kwa) == True:
			if int(kwa) in range(len(logic.globalDict["BLENDS"])):
				map = logic.globalDict["BLENDS"][int(kwa)]

		if map in logic.globalDict["BLENDS"]:
			logic.globalDict["CURRENT"]["Level"] = map
			logic.startGame(logic.expandPath("//MAPS/"+map))
			return "LOAD"
		ERROR()
		return False

	if len(args) == 1:
		OPEN(["", "list"])
		logic.CLASS.NEWLINE("'.blend' suffix not required, accepts numbers", 2, 1, (0.7,0.5,0.7,1))
		logic.CLASS.ENTRYLINE(["MAP"])
		logic.CLASS.prompt = OPEN
		return

	if "list" in args:
		for i in range(len(logic.globalDict["BLENDS"])):
			map = logic.globalDict["BLENDS"][i]
			split = map.split(".blend")
			logic.CLASS.NEWLINE(str(i)+": "+split[0], 1, 1, (1,1,1,1))
		logic.CLASS.NEWLINE()
		return

	for i in args:
		split = i.split(" ")

		if split[0] == "map" and len(split) == 2:
			map = split[1]+".blend"

			if checkNumber(split[1]) == True:
				if int(split[1]) in range(len(logic.globalDict["BLENDS"])):
					map = logic.globalDict["BLENDS"][int(split[1])]

			if map in logic.globalDict["BLENDS"]:
				logic.globalDict["CURRENT"]["Level"] = map
				logic.startGame(logic.expandPath("//MAPS/"+map))
				logic.CLASS.NEWLINE("LOADING...", 2, 2, (1,1,1,1))
				return
	ERROR()


