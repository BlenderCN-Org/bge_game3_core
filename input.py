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

from . import config


## Mouse ##
events.MOUSEMOVE = {"Old":(0.5,0.5), "Move":(0,0), "Position":(0.5,0.5)}
MS_CENTER = False
WIN_DIM = (render.getWindowWidth(), render.getWindowHeight())

## Find Available Gamepads ##
events.JOYBUTTONS = {}
events.AXISCALIBRATION = {}
JOY_CALIBRATE = None

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
			events.AXISCALIBRATION[AXIS] = 0.0

		for HAT in range(len(logic.joysticks[JOYID].hatValues)):
			events.JOYBUTTONS[JOYID]["Hats"][HAT] = {"U":0, "D":0, "L":0, "R":0}


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
		modkey = []
		for m in ["SHIFT", "CTRL", "ALT"]:
			modkey.append("LEFT"+m+"KEY")
			modkey.append("RIGHT"+m+"KEY")

		if self.input == None:
			self.device = logic.keyboard
			self.isWheel = False
			self.isModkey = False

		elif self.input_name in modkey:
			self.device = logic.keyboard
			self.isWheel = False
			self.isModkey = True

		elif self.input_name in ["LEFTMOUSE", "MIDDLEMOUSE", "RIGHTMOUSE"]:
			self.device = logic.mouse
			self.isWheel = False
			self.isModkey = False

		elif self.input_name in ["WHEELDOWNMOUSE", "WHEELUPMOUSE", "MOUSEX", "MOUSEY"]:
			self.device = logic.mouse
			self.isWheel = True
			self.isModkey = False

		else:
			self.device = logic.keyboard
			self.isWheel = False
			self.isModkey = False

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
			logic.getSceneList()[0].pre_draw.insert(0, GAMEPADDER)
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
		if self.isModkey == True:
			return True

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
	def active(self, exlusive=False):
		if self.checkInput(logic.KX_INPUT_ACTIVE) == True:
			return True
		elif exlusive == True:
			return False
		elif self.checkInput(logic.KX_INPUT_JUST_ACTIVATED) == True:
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

		if key == True:
			if self.active(False) == True:
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

	def __init__(self, SPEED=25, SMOOTH=10, TURN=0.035):
		self.getScreenRatio()
		self.updateSpeed(SPEED, SMOOTH, TURN)
		self.center()

	def getScreenRatio(self):
		global WIN_DIM
		WIN_DIM = (render.getWindowWidth(), render.getWindowHeight())
		self.screen = list(WIN_DIM)
		self.ratio = WIN_DIM[1]/WIN_DIM[0]

	def updateSpeed(self, speed=None, smooth=None, turn=None):
		if speed != None:
			self.input = speed
		if smooth != None:
			self.smoothing = int(smooth)
		if turn != None:
			self.ts_rate = turn

	def getData(self):
		dict = {
			"Speed":self.input,
			"Smooth":self.smoothing,
			"TurnRate":self.ts_rate
			}
		return dict

	def setData(self, dict):
		speed = dict.get("Speed", None)
		smooth = dict.get("Smooth", None)
		turn = dict.get("TurnRate", None)
		self.updateSpeed(speed, smooth, turn)

	def bufferReset(self):
		que = [0]*self.smoothing
		self.old_input = [que.copy(), que.copy()]

	def bufferAxis(self, axis):
		AVG = 0

		for a in range(self.smoothing):
			AVG += self.old_input[axis][a]

		return AVG/self.smoothing

	def center(self):
		global MS_CENTER
		MS_CENTER = True

		self.bufferReset()
		self.ts_input = [0, 0]
		self.skip = 10

	def smoothAxis(self, X, Y):
		turn = [0]*2
		look = Vector((X, Y))

		for i in [0,1]:
			turn[i] = look[i]
			if self.smoothing > 1:
				if look.length <= 0 and config.MOUSE_BUFFER == False:
					self.bufferReset()
				else:
					self.old_input[i].insert(0, look[i])
					self.old_input[i].pop()
				turn[i] = self.bufferAxis(i)

		return turn

	def axis(self, look=None, ui=False, center=True):
		global MS_CENTER
		MS_CENTER = center

		if self.skip > 0:
			self.skip -= 1
			return (0,0)

		RAW_X, RAW_Y = events.MOUSEMOVE["Move"]

		if ui == True:
			return (RAW_X, RAW_Y)

		X = RAW_X*(self.input/-5)
		Y = RAW_Y*(self.input/5)*self.ratio

		if look != None:
			X += look[0]*self.ts_rate
			Y += look[1]*self.ts_rate

		X, Y = self.smoothAxis(X, Y)

		return (X, Y)


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
	global MS_CENTER, WIN_DIM, JOY_CALIBRATE

	NEW_X, NEW_Y = logic.mouse.position
	OLD_X, OLD_Y = events.MOUSEMOVE["Old"]

	if getattr(config, "MOUSE_FIX", False) == True:
		NEW_X = (NEW_X*WIN_DIM[0])/(WIN_DIM[0]-1)
		NEW_Y = (NEW_Y*WIN_DIM[1])/(WIN_DIM[1]-1)

	events.MOUSEMOVE["Move"] = (NEW_X-OLD_X, OLD_Y-NEW_Y)
	events.MOUSEMOVE["Old"] = (NEW_X, NEW_Y)

	events.MOUSEMOVE["Position"] = (NEW_X-0.5, 0.5-NEW_Y)

	if MS_CENTER == True:
		if abs(NEW_X-0.5) > 0.25 or abs(NEW_Y-0.5) > 0.25:
			logic.mouse.position = (0.5, 0.5)
			events.MOUSEMOVE["Old"] = (0.5, 0.5)
	MS_CENTER = False

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
			BIAS = events.AXISCALIBRATION

			RAWINPUT = logic.joysticks[JOYID].axisValues[A]

			if JOY_CALIBRATE in ["ALL", A]: #and abs(RAWINPUT) < 0.5:
				print("AXIS CALIBRATED:", JOYID, A, -RAWINPUT)
				BIAS[A] = -RAWINPUT

			DICT[A]["VALUE"] = RAWINPUT+BIAS[A]

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

	JOY_CALIBRATE = None


print("input.py Imported")

