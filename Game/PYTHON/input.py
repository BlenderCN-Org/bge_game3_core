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

## INPUT PROCESSING ##


from bge import logic, events, render

from mathutils import Vector
import json

import PYTHON.config as config

## Find Available Gamepads ##
events.JOYBUTTONS = {}

for JOYID in range(len(logic.joysticks)):
	if logic.joysticks[JOYID] != None:
		events.JOYBUTTONS[JOYID] = {"Buttons":{}, "Axis":{}, "Hats":{}}
		print("Gamepad Found:", logic.joysticks[JOYID], "ID:", JOYID)

		for BUTID in range(logic.joysticks[JOYID].numButtons):
			events.JOYBUTTONS[JOYID]["Buttons"][BUTID] = 0
		events.JOYBUTTONS[JOYID]["Buttons"]["U"] = 0
		events.JOYBUTTONS[JOYID]["Buttons"]["D"] = 0
		events.JOYBUTTONS[JOYID]["Buttons"]["L"] = 0
		events.JOYBUTTONS[JOYID]["Buttons"]["R"] = 0

		for AXIS in range(len(logic.joysticks[JOYID].axisValues)):
			events.JOYBUTTONS[JOYID]["Axis"][AXIS] = {"NEG":0, "POS":0, "SLIDER":0, "VALUE":0.0}

		for HAT in range(len(logic.joysticks[JOYID].hatValues)):
			events.JOYBUTTONS[JOYID]["Hats"][HAT] = {"U":0, "D":0, "L":0, "R":0}


## SAVE/LOAD ##
def SaveBinds(binds, path, profile):
	dict = {}
	for key in binds:
		if getattr(binds[key], "id", None) != None:
			dict[key] = binds[key].getData()

	name = path+profile+"Keymap.cfg"
	file = open(name, "w")

	json.dump(dict, file, indent="\t")

	file.close()
	print("NOTICE: Keybinds Saved...\n\t", name)

def LoadBinds(binds, path, profile):
	name = path+profile+"Keymap.cfg"
	try:
		file = open(name, "r")
	except OSError:
		print("ERROR: File not Found...\n\t", name)
		return

	dict = json.load(file)

	file.close()

	for key in binds:
		if getattr(binds[key], "id", None) != None and key in dict:
			binds[key].setData(dict[key])

	print("NOTICE: Keybinds Loaded...\n\t", name)


## EXTRAS ##
def ClipAxis(value):
	LZ = 0.2
	HZ = 1.0

	if value < LZ:
		value = LZ
	if value > HZ:
		value = HZ

	value = ( (value-LZ)*(1/(HZ-LZ)) )

	return value

def JoinAxis(VX=0, VY=0, VZ=0):
	vec = Vector([VX, VY, VZ])

	CLIP = ClipAxis(vec.length)
	NORM = vec.normalized()*CLIP

	return NORM


## Base Class for Inputs ##
class KeyBase:

	GROUP = "Default"

	def __init__(self, ID, KEY, SIMPLE, JOYINDEX=0, JOYBUTTON=None, JOYAXIS=(None, "SLIDER", "A"), SHIFT=None, CTRL=None, ALT=None):
		self.id = ID
		self.simple_name = SIMPLE
		self.gamepad = {}
		self.modifiers = {"S":SHIFT, "C":CTRL, "A":ALT}

		self.updateBind(KEY)
		self.updateGamepad(Index=JOYINDEX, Button=JOYBUTTON, Axis=JOYAXIS[0], Type=JOYAXIS[1], Curve=JOYAXIS[2])
		self.sceneGamepadCheck()

	def updateBind(self, NEWKEY):
		self.input_name = NEWKEY

		if NEWKEY != "NONE":
			self.input = getattr(events, self.input_name)
		else:
			self.input = None

		self.autoDevice()

	def autoDevice(self):
		if self.input == None:
			self.device = logic.keyboard
			self.isWheel = False

		elif self.input_name in ["LEFTMOUSE", "MIDDLEMOUSE", "RIGHTMOUSE"]:
			self.device = logic.mouse
			self.isWheel = False

		elif self.input_name in ["WHEELDOWNMOUSE", "WHEELUPMOUSE", "MOUSEX", "MOUSEY"]:
			self.device = logic.mouse
			self.isWheel = True

		else:
			self.device = logic.keyboard
			self.isWheel = False

	def updateGamepad(self, **kwargs):
		for kw in kwargs:
			self.gamepad[kw] = kwargs[kw]

		JOYID = self.gamepad["Index"]
		BUTID = self.gamepad["Button"]
		AXIS = self.gamepad["Axis"]

		self.joy_index = JOYID

		if JOYID >= len(logic.joysticks):
			self.joy_index = None
		elif logic.joysticks[JOYID] == None:
			self.joy_index = None
		else:
			if AXIS != None:
				if AXIS >= len(logic.joysticks[JOYID].axisValues):
					self.joy_index = None
			if BUTID != None:
				if type(BUTID) is int:
					if BUTID >= logic.joysticks[JOYID].numButtons:
						self.joy_index = None
				if type(BUTID) is str:
					if len(logic.joysticks[JOYID].hatValues) <= 0:
						self.joy_index = None

	def getData(self):
		joy = self.gamepad
		mod = self.modifiers

		dict = {
		"Key": self.input_name,
		"Gamepad": joy.copy(),
		"Modifiers": mod.copy(),
		}

		return dict

	def setData(self, dict):
		self.gamepad = dict["Gamepad"].copy()
		self.modifiers = dict["Modifiers"].copy()

		self.updateBind(dict["Key"])
		self.updateGamepad()

	def sceneGamepadCheck(self):
		if GAMEPADDER not in logic.getSceneList()[0].pre_draw:
			logic.getSceneList()[0].pre_draw.append(GAMEPADDER)
			print("NOTICE: GAMEPADDER() Scene Fix -", logic.getSceneList()[0].name)
			GAMEPADDER()
			return False

		return True

	def checkInput(self, INPUT):
		if self.sceneGamepadCheck() == False:
			return False

		JOYID = self.joy_index
		BUTID = self.gamepad["Button"]
		AXIS = self.gamepad["Axis"]
		TYPE = self.gamepad["Type"]
		CURVE = self.gamepad["Curve"]

		PAD = False
		KEY = False

		## Check Gamepad ##
		if JOYID != None:
			if BUTID != None:
				if events.JOYBUTTONS[JOYID]["Buttons"][BUTID] == INPUT:
					PAD = True

			if AXIS != None and CURVE == "B":
				if events.JOYBUTTONS[JOYID]["Axis"][AXIS][TYPE] == INPUT:
					PAD = True

		elif INPUT == logic.KX_INPUT_NONE:
			PAD = True

		## Check Keyboard/Mouse ##
		if self.checkModifiers() == True or INPUT == logic.KX_INPUT_NONE:
			if self.input != None:
				if self.device.events[self.input] == INPUT:
					KEY = True

				if self.isWheel == True:
					if INPUT == logic.KX_INPUT_JUST_ACTIVATED:
						if self.device.events[self.input] == logic.KX_INPUT_ACTIVE:
							KEY = True
					if INPUT == logic.KX_INPUT_ACTIVE:
						if self.device.events[self.input] == logic.KX_INPUT_JUST_ACTIVATED:
							KEY = True

		## Returns ##
		if INPUT == logic.KX_INPUT_NONE:
			if KEY == True and PAD == True:
				return True
		else:
			if KEY == True or PAD == True:
				return True

		return False

	def checkModifiers(self):
		KEYBOARD = logic.keyboard.events
		ACTIVE = logic.KX_INPUT_ACTIVE

		S = False
		C = False
		A = False

		if self.modifiers["S"] == None:
			S = None
		elif KEYBOARD[events.LEFTSHIFTKEY] == ACTIVE or KEYBOARD[events.RIGHTSHIFTKEY] == ACTIVE:
			S = True

		if self.modifiers["C"] == None:
			C = None
		elif KEYBOARD[events.LEFTCTRLKEY] == ACTIVE or KEYBOARD[events.RIGHTCTRLKEY] == ACTIVE:
			C = True

		if self.modifiers["A"] == None:
			A = None
		elif KEYBOARD[events.LEFTALTKEY] == ACTIVE or KEYBOARD[events.RIGHTALTKEY] == ACTIVE:
			A = True

		if self.input == None:
			if S == None and C == None and A == None:
				return False

		if self.modifiers["S"] == S and self.modifiers["C"] == C and self.modifiers["A"] == A:
			return True

		return False

	## KEY EVENTS ##
	def active(self):
		if self.checkInput(logic.KX_INPUT_ACTIVE) == True:
			return True

		return False

	def tap(self):
		if self.checkInput(logic.KX_INPUT_JUST_ACTIVATED) == True:
			return True

		return False

	def released(self):
		if self.checkInput(logic.KX_INPUT_JUST_RELEASED) == True:
			return True

		return False

	def inactive(self):
		if self.checkInput(logic.KX_INPUT_NONE) == True:
			return True

		return False

	def axis(self, key=False, clip=False):
		if self.sceneGamepadCheck() == False:
			return 0.0

		JOYID = self.joy_index
		AXIS = self.gamepad["Axis"]
		TYPE = self.gamepad["Type"]
		CURVE = self.gamepad["Curve"]

		if self.checkInput(logic.KX_INPUT_ACTIVE) == True and key == True:
			return 1.0
		if JOYID == None or AXIS == None or CURVE == "B":
			return 0.0

		VALUE = events.JOYBUTTONS[JOYID]["Axis"][AXIS]["VALUE"]
		ABSVAL = abs(VALUE)
		if clip == True:
			ABSVAL = ClipAxis(ABSVAL)

		if TYPE == "POS":
			if VALUE > 0:
				return ABSVAL

		elif TYPE == "NEG":
			if VALUE < 0:
				return ABSVAL

		elif TYPE == "SLIDER":
			if VALUE > 0:
				SLIDER = (VALUE+1)*0.5
				return SLIDER

		return 0.0


## Mouse Look Base Class ##
class MouseLook:

	def __init__(self, SPEED, SMOOTH=10):
		self.getScreenRatio()
		self.updateSpeed(SPEED, SMOOTH)
		self.center()

	def getScreenRatio(self):
		self.screen = (render.getWindowWidth(), render.getWindowHeight())
		self.ratio = self.screen[1]/self.screen[0]

	def updateSpeed(self, SPEED=None, SMOOTH=None):
		if SPEED != None:
			self.input = SPEED
		if SMOOTH != None:
			self.smoothing = int(SMOOTH)

	def center(self):
		self.OLD_X = [0]*self.smoothing
		self.OLD_Y = [0]*self.smoothing

		logic.mouse.position = (0.5, 0.5)
		self.skip = True

	def axis(self, ui=False):
		if self.skip == True:
			self.skip = False
			logic.mouse.position = (0.5, 0.5)
			return (0,0)

		RAW_X, RAW_Y = logic.mouse.position

		if config.UPBGE_FIX == True:
			RAW_X = (RAW_X*self.screen[0])/(self.screen[0]-1)
			RAW_Y = (RAW_Y*self.screen[1])/(self.screen[1]-1)

		if ui == True:
			X = (RAW_X-0.5)
			Y = (0.5-RAW_Y)
			logic.mouse.position = (0.5, 0.5)
			return (X,Y)

		elif self.smoothing > 1:
			NEW_X = (0.5-RAW_X)*2
			NEW_Y = (0.5-RAW_Y)*2

			AVG_X = 0
			AVG_Y = 0

			for IX in range(self.smoothing):
				AVG_X += self.OLD_X[IX]

			for IY in range(self.smoothing):
				AVG_Y += self.OLD_Y[IY]

			msX = AVG_X/self.smoothing
			msY = AVG_Y/self.smoothing

			self.OLD_X.insert(0, NEW_X)
			self.OLD_Y.insert(0, NEW_Y)
			self.OLD_X.pop()
			self.OLD_Y.pop()

		else:
			msX = (0.5-RAW_X)*2
			msY = (0.5-RAW_Y)*2

		X = msX*(self.input*0.1)
		Y = msY*(self.input*0.1)*self.ratio

		logic.mouse.position = (0.5, 0.5)

		return (X,Y)


class NumPad:

	def __init__(self):

		self.numkeys = {
			"0": events.PAD0,
			"1": events.PAD1,
			"2": events.PAD2,
			"3": events.PAD3,
			"4": events.PAD4,
			"5": events.PAD5,
			"6": events.PAD6,
			"7": events.PAD7,
			"8": events.PAD8,
			"9": events.PAD9
			}

	def checkInput(self, INPUT):
		for key in self.numkeys:
			kbe = self.numkeys[key]
			if logic.keyboard.events[kbe] == INPUT:
				return key

		return None

	## KEY EVENTS ##
	def active(self):
		return self.checkInput(logic.KX_INPUT_ACTIVE)

	def tap(self):
		return self.checkInput(logic.KX_INPUT_JUST_ACTIVATED)

	def released(self):
		return self.checkInput(logic.KX_INPUT_JUST_RELEASED)

	def inactive(self):
		return self.checkInput(logic.KX_INPUT_NONE)

	def enter(self):
		if logic.keyboard.events[events.PADENTER] == logic.KX_INPUT_JUST_ACTIVATED:
			return True
		return False


## Updates Joystick Values ##
def GAMEPADDER():

	for JOYID in events.JOYBUTTONS:

		if logic.joysticks[JOYID] == None:
			print("GAMEPAD ERROR:", JOYID, "Not Found!")
			return

		for B in events.JOYBUTTONS[JOYID]["Buttons"]:
			DICT = events.JOYBUTTONS[JOYID]["Buttons"]

			if B in logic.joysticks[JOYID].activeButtons:
				if DICT[B] == 0 or DICT[B] == 3:
					DICT[B] = 1
				else:
					DICT[B] = 2
			else:
				if DICT[B] == 2 or DICT[B] == 1:
					DICT[B] = 3
				else:
					DICT[B] = 0

		for A in events.JOYBUTTONS[JOYID]["Axis"]:
			DICT = events.JOYBUTTONS[JOYID]["Axis"]

			RAWINPUT = logic.joysticks[JOYID].axisValues[A]

			DICT[A]["VALUE"] = RAWINPUT

			if RAWINPUT > 0.5:
				if DICT[A]["POS"] == 0 or DICT[A]["POS"] == 3:
					DICT[A]["POS"] = 1
				else:
					DICT[A]["POS"] = 2
			else:
				if DICT[A]["POS"] == 2 or DICT[A]["POS"] == 1:
					DICT[A]["POS"] = 3
				else:
					DICT[A]["POS"] = 0

			if RAWINPUT < -0.5:
				if DICT[A]["NEG"] == 0 or DICT[A]["NEG"] == 3:
					DICT[A]["NEG"] = 1
				else:
					DICT[A]["NEG"] = 2
			else:
				if DICT[A]["NEG"] == 2 or DICT[A]["NEG"] == 1:
					DICT[A]["NEG"] = 3
				else:
					DICT[A]["NEG"] = 0

			if RAWINPUT > 0.0:
				if DICT[A]["SLIDER"] == 0 or DICT[A]["SLIDER"] == 3:
					DICT[A]["SLIDER"] = 1
				else:
					DICT[A]["SLIDER"] = 2
			else:
				if DICT[A]["SLIDER"] == 2 or DICT[A]["SLIDER"] == 1:
					DICT[A]["SLIDER"] = 3
				else:
					DICT[A]["SLIDER"] = 0

		for H in events.JOYBUTTONS[JOYID]["Hats"]:
			DICT = events.JOYBUTTONS[JOYID]["Hats"]
			STAT = {0:"", 1:"U", 2:"R", 3:"UR", 4:"D", 6:"DR", 8:"L", 9:"UL", 12:"DL"}
			VALUE = STAT[logic.joysticks[JOYID].hatValues[H]]

			for key in DICT[H]:
				if key in VALUE:
					if DICT[H][key] == 0 or DICT[H][key] == 3:
						DICT[H][key] = 1
					else:
						DICT[H][key] = 2
				else:
					if DICT[H][key] == 2 or DICT[H][key] == 1:
						DICT[H][key] = 3
					else:
						DICT[H][key] = 0

				events.JOYBUTTONS[JOYID]["Buttons"][key] = DICT[H][key]


print("input.py Imported")

