

import json

from mathutils import Vector, Matrix

from bge import logic, events, render

from game3 import keymap, input, config



def RUN(cont):
	if "Class" in cont.owner and logic.FREEZE == None:
		cont.owner["Class"].RUN()


def buildKeys(cont):

	logic.FREEZE = None

	render.showFramerate(False)
	render.showProfile(False)
	render.showProperties(False)

	owner = cont.owner
	scene = owner.scene

	profile = logic.globalDict["CURRENT"]["Profile"]
	scene.objects["Profile"].text = "Profile:"
	scene.objects["Name"].text = profile

	if "_" in profile:
		profile = "Base"

	input.LoadBinds(keymap.BINDS, logic.globalDict["DATA"]["GAMEPATH"], profile)

	owner["KEYLIST"] = []
	owner["OBJECTS"] = []

	for key in keymap.BINDS:
		cls = keymap.BINDS[key]
		if getattr(cls, "id", None) != None:
			owner["KEYLIST"].append(cls)

	owner["KEYLIST"].sort( key=lambda x: x.id )
	grp = ""

	for cls in owner["KEYLIST"]:
		split = cls.id.split(".")
		if split[1] != grp:
			owner.worldPosition[1] -= 1
			obj = scene.addObject("LIST.KeyBinds.GROUP", owner, 0)
			obj.text = keymap.BINDS[split[1]]
			owner.worldPosition[1] -= 2
			owner["OBJECTS"].append(obj)
			grp = split[1]

		obj = scene.addObject("LIST.KeyBinds", owner, 0)
		obj["Bind"] = cls
		obj["Class"] = SetBinds(obj)

		owner.worldPosition[1] -= 2
		owner["OBJECTS"].append(obj)

	owner["LENGTH"] = abs(owner.worldPosition[1])-10
	owner["SCROLL"] = 0
	owner.worldPosition = (0,0,0)

	for obj in owner["OBJECTS"]:
		#print(obj)
		obj.setParent(owner)


def manageKeys(cont):

	owner = cont.owner
	scene = owner.scene
	camera = scene.active_camera
	cursor = scene.objects["Cursor"]
	info = scene.objects["Info"]

	cursor.localPosition[0] = (logic.mouse.position[0]-0.5)*camera.ortho_scale 
	cursor.localPosition[1] = (logic.mouse.position[1]-0.5)*-camera.ortho_scale*keymap.MOUSELOOK.ratio
	cursor.localPosition[2] = -2

	if logic.FREEZE != None:
		status = logic.FREEZE()
		info.text = "Enter Valid Input... ESC to Cancel... SHIFT-ACCENT to Set 'None'..."
		if status == "END":
			logic.FREEZE = None
		return

	ms = logic.mouse.events
	wu = events.WHEELUPMOUSE
	wd = events.WHEELDOWNMOUSE

	rate = owner["SCROLL"]-owner.worldPosition[1]

	if ms[wu] in [1,2] and owner["SCROLL"] > 0:
		owner["SCROLL"] -= 2
	if ms[wd] in [1,2] and owner["SCROLL"] < owner["LENGTH"]:
		owner["SCROLL"] += 2

	owner.worldPosition[1] += rate*0.1

	rayto = cursor.worldPosition.copy()
	rayto[2] += -1

	rayOBJ = cursor.rayCastTo(rayto, camera.far, "RAYCAST")

	if rayOBJ:
		rayOBJ["RAYCAST"] = True
		split = rayOBJ.name.split(".")
		if rayOBJ.name == "Back":
			info.text = "Return to the Launcher"
		if rayOBJ.name == "Quit":
			info.text = "Exit the Utility"
		if rayOBJ.name == "Save":
			info.text = "Save the Current Configuration"
			if ms[events.LEFTMOUSE] == 1:
				profile = logic.globalDict["CURRENT"]["Profile"]
				if "_" in profile:
					profile = "Base"

				input.SaveBinds(keymap.BINDS, logic.globalDict["DATA"]["GAMEPATH"], profile)

		if len(split) >= 3:
			name = split[2]
			if name == "KEY":
				info.text = "Click to re-bind Keyboard Key"
			if name == "DEV":
				info.text = "Index of the Joystick to Use"
			if name == "BUT":
				info.text = "Joystick Button Index"
			if name == "AXIS":
				info.text = "Joystick Axis Index"
			if name == "AXIS_TYPE":
				info.text = "Axis Response Range, [^] Use Positive Range, [v] Use Negative Range, [<>] Use Full Range as 0-1."
			if name == "AXIS_CURVE":
				info.text = "Axis Type, Normal or Button Mode.  If Button Mode, Triggers as Key Press at 50%."
			if name == "SWITCH":
				info.text = "Switch the UI for Gamepad or Keyboard Config."
			if "MOD_" in name:
				info.text = "Set Shift/Ctrl/Alt Modifier Conditions.  Blue Requires Modifier to be Pressed, Red Requires Released, Gray Ignores."
	else:
		info.text = ""

	scene.objects["Save"]["RAYCAST"] = False


class SetBinds:

	ORI_CLR = ((1, 0, 0), (0, 1, 0), (0, 0, 1))
	ORI_POS = ((0, 0, -1), (0, 1, 0), (1, 0, 0))
	ORI_NEG = ((0, 0, 1), (0, 1, 0), (-1, 0, 0))
	ORI_NONE = ((0, 0, 0), (0, 0, 0), (0, 0, 0))
	ORI_FLIP = ((1, 0, 0), (0, -1, 0), (0, 0, -1))

	COL_ICO = (0.7, 0.7, 0.7, 1)
	COL_ON = (0.0, 0.3, 0.5, 1)
	COL_OFF = (0.3, 0.3, 0.3, 1)

	def getString(self, arg):
		if arg == None:
			return "~"
		return str(arg)

	def __init__(self, owner):
		self.switch = False
		self.axsv = None
		self.bind = owner["Bind"]
		bind = self.bind

		self.objects = {"Root":owner}

		for child in owner.childrenRecursive:
			name = child.name.split(".")[2]
			self.objects[name] = child

		self.objects["NAME"].text = bind.simple_name
		self.objects["KEY_VALUE"].text = bind.input_name
		self.objects["DEV_VALUE"].text = self.getString(bind.gamepad["Index"])
		self.objects["BUT_VALUE"].text = self.getString(bind.gamepad["Button"])
		self.objects["AXIS_VALUE"].text = self.getString(bind.gamepad["Axis"])

		self.objects["MOD_SHIFT"].color = self.getModifierColor("S")
		self.objects["MOD_CTRL"].color = self.getModifierColor("C")
		self.objects["MOD_ALT"].color = self.getModifierColor("A")

		self.objects["AXIS_TYPE"].localOrientation = self.getAxisTypeOri()
		self.objects["AXIS_CURVE"].localOrientation = self.getAxisCurveOri()

	def getModifierColor(self, key):
		modifiers = self.bind.modifiers
		if modifiers[key] == True:
			return Vector((0, 0.4, 0.8, 1))
		if modifiers[key] == False:
			return Vector((0.6, 0, 0, 1))
		if modifiers[key] == None:
			return Vector((0.5, 0.5, 0.5, 1))

	def setModifier(self, key):
		modifiers = self.bind.modifiers
		if modifiers[key] == None:
			modifiers[key] = True
		elif modifiers[key] == True:
			modifiers[key] = False
		elif modifiers[key] == False:
			modifiers[key] = None

	def getAxisTypeOri(self):
		gamepad = self.bind.gamepad
		if gamepad["Axis"] == None:
			return self.ORI_FLIP
		if gamepad["Type"] == "SLIDER":
			return self.ORI_CLR
		if gamepad["Type"] == "POS":
			return self.ORI_POS
		if gamepad["Type"] == "NEG":
			return self.ORI_NEG

	def setAxisType(self):
		gamepad = self.bind.gamepad
		if gamepad["Axis"] == None:
			return
		if gamepad["Type"] == "POS":
			gamepad["Type"] = "NEG"
		elif gamepad["Type"] == "NEG":
			gamepad["Type"] = "SLIDER"
		elif gamepad["Type"] == "SLIDER":
			gamepad["Type"] = "POS"

	def getAxisCurveOri(self):
		gamepad = self.bind.gamepad
		if gamepad["Axis"] == None:
			return self.ORI_FLIP
		if gamepad["Curve"] == "A":
			return self.ORI_POS
		if gamepad["Curve"] == "B":
			return self.ORI_NEG

	def setAxisCurve(self):
		gamepad = self.bind.gamepad
		if gamepad["Axis"] == None:
			return
		if gamepad["Curve"] == "A":
			gamepad["Curve"] = "B"
		elif gamepad["Curve"] == "B":
			gamepad["Curve"] = "A"

	def setKey(self):
		self.objects["KEY"].color = (0, 0.5, 1, 1)
		self.objects["KEY_VALUE"].color = (1,1,1,1)
		self.objects["KEY_VALUE"].text = "Press New Key..."

		KEY = "WAIT"
		for x in logic.keyboard.events:
			if logic.keyboard.events[x] == 1 and x != events.ESCKEY:
				KEY = events.EventToString(x)
				for m in ["SHIFT", "CTRL", "ALT"]:
					if m in KEY:
						return

		for y in logic.mouse.events:
			if y not in [events.MOUSEX, events.MOUSEY]:
				if logic.mouse.events[y] == 1:
					KEY = events.EventToString(y)

		if logic.keyboard.events[events.ACCENTGRAVEKEY] == 1:
			if logic.keyboard.events[events.LEFTSHIFTKEY] == 2 or logic.keyboard.events[events.RIGHTSHIFTKEY] == 2:
				KEY = "NONE"

		if KEY != "WAIT":
			self.bind.updateBind(KEY)
			KEY = "DONE"

		if logic.keyboard.events[events.ESCKEY] == 1 or KEY == "DONE":
			self.objects["KEY_VALUE"].text = self.bind.input_name
			self.objects["KEY_VALUE"].color = (0.5, 0.5, 0.5, 1)
			return "END"

	def setJoyButton(self):
		if logic.joysticks[self.bind.gamepad["Index"]] == None:
			return "END"
		self.objects["BUT"].color = (0, 0.5, 1, 1)
		self.objects["BUT_VALUE"].color = (1,1,1,1)
		self.objects["BUT_VALUE"].text = "_"

		data = events.JOYBUTTONS[self.bind.gamepad["Index"]]["Buttons"]
		BUTID = "WAIT"

		for B in data:
			if data[B] == 1:
				BUTID = B

		if logic.keyboard.events[events.ACCENTGRAVEKEY] == 1:
			if logic.keyboard.events[events.LEFTSHIFTKEY] == 2 or logic.keyboard.events[events.RIGHTSHIFTKEY] == 2:
				BUTID = None

		if BUTID != "WAIT":
			self.bind.updateGamepad(Button=BUTID)
			BUTID = "DONE"

		if logic.keyboard.events[events.ESCKEY] == 1 or BUTID == "DONE":
				self.objects["BUT_VALUE"].text = self.getString(self.bind.gamepad["Button"])
				self.objects["BUT_VALUE"].color = (0.7, 0.7, 0.7, 1)
				return "END"

	def setJoyAxis(self):
		if logic.joysticks[self.bind.gamepad["Index"]] == None:
			return "END"
		self.objects["AXIS"].color = (0, 0.5, 1, 1)
		self.objects["AXIS_VALUE"].color = (1,1,1,1)
		self.objects["AXIS_VALUE"].text = "_"

		data = logic.joysticks[self.bind.gamepad["Index"]]
		AXIS = "WAIT"

		if self.axsv == None:
			self.axsv = []
			for v in data.axisValues:
				self.axsv.append(v)
				
		for i in range(len(data.axisValues)):
			if abs(data.axisValues[i]-self.axsv[i]) > 0.4:
				AXIS = i

		if logic.keyboard.events[events.ACCENTGRAVEKEY] == 1:
			if logic.keyboard.events[events.LEFTSHIFTKEY] == 2 or logic.keyboard.events[events.RIGHTSHIFTKEY] == 2:
				AXIS = None

		if AXIS != "WAIT":
			self.bind.updateGamepad(Axis=AXIS)
			self.axsv = None
			AXIS = "DONE"

		if logic.keyboard.events[events.ESCKEY] == 1 or AXIS == "DONE":
				self.objects["AXIS_VALUE"].text = self.getString(self.bind.gamepad["Axis"])
				self.objects["AXIS_VALUE"].color = (0.7, 0.7, 0.7, 1)
				return "END"

	def RUN(self):
		objects = self.objects
		click = logic.mouse.events[events.LEFTMOUSE]
		txt_list = ["KEY", "DEV", "BUT", "AXIS"]
		ico_list = ["SWITCH", "AXIS_TYPE", "AXIS_CURVE"]

		for key in objects:
			obj = objects[key]
			ray = obj.get("RAYCAST", None)
			if ray == True:
				if key in txt_list:
					obj.color = self.COL_ON
				if key in ico_list:
					obj.color = (1,1,1,1)

				if key == "MOD_SHIFT":
					obj.color = self.getModifierColor("S")*2
					if click == 1:
						self.setModifier("S")
				if key == "MOD_CTRL":
					obj.color = self.getModifierColor("C")*2
					if click == 1:
						self.setModifier("C")
				if key == "MOD_ALT":
					obj.color = self.getModifierColor("A")*2
					if click == 1:
						self.setModifier("A")

				if click == 1:
					if key == "KEY":
						logic.FREEZE = self.setKey
					if key == "BUT":
						logic.FREEZE = self.setJoyButton
					if key == "AXIS":
						logic.FREEZE = self.setJoyAxis
					if key == "SWITCH":
						if self.switch == False:
							objects["BG"].localOrientation = self.ORI_FLIP
							self.switch = True
						else:
							objects["BG"].localOrientation = self.ORI_CLR
							self.switch = False

			elif ray == False:
				if key in txt_list:
					obj.color = self.COL_OFF
				if key in ico_list:
					obj.color = self.COL_ICO

				if key == "MOD_SHIFT":
					obj.color = self.getModifierColor("S")
				if key == "MOD_CTRL":
					obj.color = self.getModifierColor("C")
				if key == "MOD_ALT":
					obj.color = self.getModifierColor("A")

			if key == "AXIS_TYPE":
				if ray == True and click == 1:
					self.setAxisType()
				obj.localOrientation = self.getAxisTypeOri()
			if key == "AXIS_CURVE":
				if ray == True and click == 1:
					self.setAxisCurve()
				obj.localOrientation = self.getAxisCurveOri()
			if "RAYCAST" in obj:
				obj["RAYCAST"] = False

