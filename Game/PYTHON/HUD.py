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

## HUD ##


from bge import logic

import PYTHON.keymap as keymap
import PYTHON.base as base

from mathutils import Vector

logic.HUDCLASS = None

if "CURRENT" in logic.globalDict:
	logic.addScene("HUD", 1)


def START(cont):
	owner = cont.owner
	scene = owner.scene

	base.SC_HUD = scene

	scene.post_draw.append(base.settings.SCREENSHOT)

	print("Loading HUD...")

	logic.LibLoad( base.DATA["GAMEPATH"]+"CONTENT\\Game Assets HUD.blend", "Scene", load_actions=True, verbose=False, load_scripts=False)

	logic.HUDCLASS.doBlackOut()


def RUN(cont):
	scene = cont.owner.scene

	if logic.HUDCLASS != None and logic.PLAYERCLASS != None:
		logic.HUDCLASS.RUN()


class CoreHUD(base.CoreObject):

	UPDATE = False
	OBJECT = "None"

	def __init__(self, prefix):
		scene = base.SC_HUD
		owner = scene.addObject(prefix+self.OBJECT, scene.objects["HUD.START"], 0)

		self.objects = {"Root":owner}

		self.data = self.defaultData()

		self.active_pre = []
		self.active_state = self.ST_Active
		self.active_post = []

		self.findObjects()

		self.ST_Startup()

	def findObjects(self):
		obj = self.objects["Root"]
		dict = self.objects
		group = []
		list = []

		for child in obj.childrenRecursive:
			split = child.name.split(".")
			name = None

			if len(split) > 1:
				name = split[1]

			if name != None and name in list:
				if name not in group:
					group.append(name)

			if len(split) > 2:
				dict[split[1]] = {}
				if split[1] not in group:
					group.append(split[1])

			if name != None:
				list.append(name)

		for child in obj.childrenRecursive:
			split = child.name.split(".")
			if len(split) > 1:
				if split[1] in group:
					if len(split) <= 2:
						dict[split[1]][""] = child
					elif split[2] != "":
						dict[split[1]][split[2]] = child
				else:
					dict[split[1]] = child

	def destroy(self):
		self.objects["Root"].endObject()
		self.objects["Root"] = None


class Compass(CoreHUD):

	OBJECT = "Compass"

	def ST_Startup(self):
		RES = logic.globalDict["GRAPHICS"]["Resolution"]
		self.objects["Cam"].setViewport(0, 0, RES[0], RES[1])
		self.compass = None

	def ST_Active(self):
		cp_comp = self.objects["Direction"]
		cp_dist = self.objects["Distance"]

		if self.compass == None:
			target = [0, 10000, 0]
		else:
			target = self.compass

		if base.SC_SCN.active_camera.parent != None:
			origin = base.SC_SCN.active_camera.parent
			vd, vg, vl = origin.getVectTo(target)
			vl = [vl[0], vl[1], vl[2]]
		else:
			origin = base.SC_SCN.active_camera
			vd, vg, vl = origin.getVectTo(target)
			vl = [vl[0], vl[2]*-1, vl[1]]

		cp_comp.alignAxisToVect(vl, 1, 0.3)
		cp_comp.alignAxisToVect((0,0,1), 2, 1.0)

		if vd < 800:
			cp_dist.color[1] = 1-(((vd*0.00125)*0.8)+0.2)
		else:
			cp_dist.color[1] = 0


class Annotation(CoreHUD):

	OBJECT = "Annotation"

	def ST_Startup(self):
		self.textlist = None
		self.objlist = []
		self.timer = 0
		self.current = 0

		RES = logic.globalDict["GRAPHICS"]["Resolution"]
		self.objects["Cam"].setViewport(0, 0, RES[0], RES[1])
		self.objects["Cam"].useViewport = True

	def destroy(self):
		self.objects["Cam"].useViewport = False

		for obj in self.objlist:
			obj.endObject()

		self.objects["Root"].endObject()
		self.objects["Root"] = None

	def setSubtitle(self, subt):
		for obj in self.objlist:
			obj.endObject()

		self.textlist = subt
		self.timer = 0
		self.current = 0
		self.objlist = []

	def getChild(self, obj, name):
		child = obj.children["UI_Annotation"+name]
		return child

	def ST_Active(self):
		fade = False
		if self.textlist != None:
			OBJ = self.objects["List"]
			CUR = self.textlist[self.current]

			if self.timer == 0:
				root = scene.addObject("UI_Annotation", OBJ, 0)
				self.getChild(root, "NameText").color = (CUR["COLOR"][0], CUR["COLOR"][1], CUR["COLOR"][2], 0)
				self.getChild(root, "NameText").text = CUR["NAME"]
				self.getChild(root, "NameMesh").color = (0, 0, 0, 0.5)
				self.getChild(root, "LineText").color = (0.8, 0.8, 0.8, 0)
				self.getChild(root, "LineText").text = CUR["LINE"]
				self.getChild(root, "LineMesh").localScale[1] = len(CUR["LINE"].split("\n"))

				self.objlist.append(root)

			if len(self.objlist) >= 2:
				fade = True

			self.timer += 1

			if self.timer > abs(CUR["TIME"])+30:
				self.timer = 0
				self.current += 1
				if self.current >= len(self.textlist):
					self.textlist = None
					self.current = 0

			elif self.timer <= 30:
				alpha = self.timer/30
				root = self.objlist[-1]
				self.getChild(root, "NameMesh").color[3] = alpha*0.5
				self.getChild(root, "NameText").color[3] = alpha
				self.getChild(root, "LineMesh").color[3] = alpha*0.5
				self.getChild(root, "LineText").color[3] = alpha

				for box in self.objlist:
					hgt = 1.5+(self.getChild(root, "LineMesh").localScale[1])
					box.localPosition[1] += hgt*(1/30)

		elif len(self.objlist) >= 1:
			self.timer += 1
			fade = True
			if self.timer > 30:
				self.timer = 0

		if fade == True:
			if self.timer == 30:
				self.objlist.pop(0).endObject()
			elif self.timer < 30:
				alpha = 1-(self.timer/30)
				root = self.objlist[0]
				self.getChild(root, "NameMesh").color[3] = alpha*0.5
				self.getChild(root, "NameText").color[3] = alpha
				self.getChild(root, "LineMesh").color[3] = alpha*0.5
				self.getChild(root, "LineText").color[3] = alpha


class Interact(CoreHUD):

	OBJECT = "Interact"

	def ST_Startup(self):
		self.boot_timer = 0

	def ST_Active(self, plr):

		text = plr.data["HUD"]["Text"]
		color = plr.data["HUD"]["Color"]
		pos = plr.data["HUD"]["Target"]
		lock = plr.data["HUD"].get("Locked", None)

		if lock != None:
			text = "Locked!"
			color = (1,0,0,1)
			plr.data["HUD"]["Locked"] = None

		if self.boot_timer < 30:
			list = [". "]*int(self.boot_timer/3)
			text = "".join(list)
			self.boot_timer += 1

		self.objects["Text"].text = text

		plr.data["HUD"]["Text"] = ""

		if pos == None:
			self.objects["Target"].localPosition = (0, 0, 64)
		else:
			self.objects["Target"].localPosition = ((pos[0]-0.5)*64, (0.5-pos[1])*36, 0)

		self.objects["Target"].color = color


class Stats(CoreHUD):

	OBJECT = "Stats"

	def ST_Active(self, plr):
		self.objects["Name"].text = plr.NAME
		self.setStat("Health", plr.data["HEALTH"], 15)
		self.setStat("Energy", plr.data["ENERGY"], 14.1)

	def setStat(self, key, value, offset):
		bar = self.objects[key]
		txt = self.objects[key+"Text"]

		stat = value/100

		if stat < 0.1:
			txt.color = (1,0,0,1)
		elif stat > 1:
			stat = 1
			txt = (1,0,1,1)
		else:
			txt.color = (0,1,0,0.5)

		bar.color[0] = stat
		txt.localPosition[0] = offset*stat
		txt.text = str(int(round(value, 0)))


class Weapons(CoreHUD):

	OBJECT = "Weapons"

	def ST_Startup(self):
		self.weaptype = ""

	def ST_Active(self, plr):
		weap = plr.data["WPDATA"]

		mode = self.objects["Mode"]
		wpid = self.objects["ID"]
		stat = self.objects["Stat"]

		type = weap["CURRENT"]+str(weap["ACTIVE"]!="NONE")
		wheel = weap["WHEEL"][weap["CURRENT"]]

		if self.weaptype != type:
			if "MELEE" in type:
				mode.worldOrientation = self.createMatrix(mirror="XZ")
				self.weaptype = type
			if "RANGED" in type:
				mode.worldOrientation = self.createMatrix()
				self.weaptype = type

			if weap["ACTIVE"] == "NONE":
				mode.color = (0.4, 0.4, 0.4, 0.5)
				stat.color = (0.4, 0.4, 0.4, 0.5)
				wpid.color = (0.4, 0.4, 0.4, 0.5)
			else:
				mode.color = (0, 0, 0, 0.5)
				stat.color = (0, 1, 0, 0.5)
				wpid.color = (0, 1, 0, 0.5)

		ID = wheel["ID"]

		if ID == -1:
			wpid.text = ""
			SLOT = "__Fallback_WP"
		else:
			wpid.text = str(ID)
			SLOT = wheel["LIST"][ID]

		stat.text = str(plr.cls_dict[SLOT].data["HUD"]["Stat"])
		stat.worldPosition[0] = (len(stat.text)*-0.59)-2


class Inventory(CoreHUD):

	OBJECT = "Inventory"

	def defaultData(self):
		self.itemdict = {}
		return {}

	def destroy(self):
		for slot in self.itemdict:
			obj = self.itemdict[slot]

			obj["Icon"].endObject()
			if obj["Slot"] != None:
				obj["Slot"].endObject()

		self.itemdict = {}

		self.objects["Root"].endObject()
		self.objects["Root"] = None

	def ST_Active(self, plr):
		gc = []

		for slot in plr.data["INVSLOT"]:
			dict = plr.data["INVSLOT"][slot]

			if self.itemdict.get(slot, None) == None:
				name = dict["Object"]
				self.itemdict[slot] = self.newIcon(name)

				if slot in plr.data["SLOTS"]:
					key = plr.data["SLOTS"][slot]

					ic, bd = self.newSlotIcon(name, key)
					self.itemdict[slot]["Slot"] = ic
					self.itemdict[slot]["Border"] = bd

				self.itemdict[slot]["DICT"] = dict

		for slot in self.itemdict:
			obj = self.itemdict[slot]
			dict = obj["DICT"]
			data = dict["Data"]

			if dict["Equiped"] in ["DROP", None, False]:
				obj["Icon"].endObject()
				if obj["Slot"] != None:
					obj["Slot"].endObject()
				gc.append(slot)
				break

			obj["Icon"].localPosition[1] = plr.data["INVENTORY"].index(dict)*-2
			obj["Stat"].localScale[0] = -1+(data["HUD"]["Stat"]/100)
			obj["Text"].text = str(data["HUD"]["Text"])

			if data["ENABLE"] == False:
				obj["Icon"].color = (0.5, 0.5, 0.5, 1)
				obj["Text"].color[3] = 0.5
				bdcol = (0.25, 0.25, 0.25, 1)
			else:
				obj["Icon"].color = (1, 1, 1, 1)
				obj["Text"].color[3] = 1
				bdcol = (0, 0.8, 0, 1)

			if obj["Slot"] != None:
				key = plr.data["SLOTS"].get(slot, None)

				if key == None:
					obj["Slot"].endObject()
					obj["Slot"] = None
					obj["Border"] = None
				else:
					X = self.objects["INV"][key].worldPosition[0]
					obj["Slot"].localPosition[0] = X
					obj["Border"].color = bdcol

		for i in gc:
			del self.itemdict[i]

	def newIcon(self, name):
		scene = base.SC_HUD

		stack = self.objects["Items"]

		if "HUD.Icons."+name not in scene.objectsInactive:
			name = "None"
		icon = scene.objectsInactive["HUD.Icons."+name]
		stat = scene.objectsInactive["HUD.IconStat"]
		text = scene.objectsInactive["HUD.IconText"]

		iconobj = base.SC_HUD.addObject(icon, stack, 0)
		statobj = base.SC_HUD.addObject(stat, stack, 0)
		textobj = base.SC_HUD.addObject(text, stack, 0)

		iconobj.setParent(stack)
		statobj.setParent(iconobj)
		textobj.setParent(iconobj)

		statobj.localPosition = (1,-1,1)
		statobj.localScale = (0,1,1)
		statobj.color = (0, 0, 0, 0.5)
		textobj.localPosition = (0,0,0)
		textobj.color = (0, 1, 0, 0.5)

		return {"Icon":iconobj, "Stat":statobj, "Text":textobj, "Slot":None, "Border":None}

	def newSlotIcon(self, name, key):
		scene = base.SC_HUD

		place = self.objects["INV"][key]

		if "HUD.Icons."+name not in scene.objectsInactive:
			name = "None"
		icon = scene.objectsInactive["HUD.Icons."+name]
		border = scene.objectsInactive["HUD.IconBorder"]

		iconobj = base.SC_HUD.addObject(icon, place, 0)
		iconobj.worldPosition[2] += 2
		iconobj.color = (1,1,1,1)

		borderobj = base.SC_HUD.addObject(border, iconobj, 0)
		borderobj.setParent(iconobj)
		borderobj.localPosition = (0, 0, 1)
		borderobj.color = (0.25, 0.25, 0.25, 1)

		return iconobj, borderobj


class Cinema(CoreHUD):

	OBJECT = "Cinema"

	def ST_Startup(self):
		self.objects["Name"].text = ""
		self.objects["Line"].text = ""
		self.objects["Line"].localPosition[0] = 0

	def ST_Active(self, plr):
		subt = plr.data["HUD"]["Subtitles"]

		if subt == None:
			return

		self.objects["Name"].text = subt["NAME"]+":"
		self.objects["Name"].color = (subt["COLOR"][0], subt["COLOR"][1], subt["COLOR"][2], 1)
		self.objects["Line"].text = subt["LINE"]
		self.objects["Line"].localPosition[0] = (len(subt["NAME"])+2)*0.6


class Speedometer(CoreHUD):

	OBJECT = "Speedometer"

	def ST_Active(self, plr):
		root = plr.objects["Root"]
		refY = plr.data["HUD"].get("Forward", (0,1,0))
		speed = abs(root.localLinearVelocity*self.createVector(vec=refY))*2.237
		self.objects["Text"].text = str(round(speed))
		if speed > 130:
			speed = 130
		self.objects["Speed"].localOrientation = self.createMatrix(rot=[0,0,-speed], deg=True)


class Aircraft(CoreHUD):

	OBJECT = "Aircraft"

	def ST_Startup(self):
		self.old_power = 0
		self.old_lift = 0

	def ST_Active(self, plr):
		root = plr.objects["Root"]
		glbZ = self.createVector(vec=[0,0,1])

		## Roll ##
		refX = plr.data["HUD"].get("Side", (1,0,0))
		angX = root.getAxisVect(refX).angle(glbZ)
		angX = self.toDeg(angX)-90
		rscl = 0.167
		#rscl = 1.0
		self.objects["Roll"].localOrientation = self.createMatrix(rot=[0,0,angX*rscl], deg=True)

		## Pitch ##
		refY = plr.data["HUD"].get("Forward", (0,1,0))
		angY = root.getAxisVect(refY).angle(glbZ)
		angY = self.toDeg(angY)
		self.objects["Pitch"].localOrientation = self.createMatrix(rot=[angY,0,0], deg=True)

		## Power ##
		power = plr.data["HUD"].get("Power", 0)*0.2
		self.old_power += (power-self.old_power)*0.5
		self.objects["Power"].localOrientation = self.createMatrix(rot=[0,0,self.old_power], deg=True)

		## Lift ##
		lift = plr.data["HUD"].get("Lift", 0)
		self.old_lift += (lift-self.old_lift)*0.5
		self.objects["Lift"].color[0] = ((self.old_lift/100)*0.75)


class HUDLayout:

	GROUP = "Core"
	MODULES = [Stats, Interact, Inventory, Weapons]

	def __init__(self):
		self.modlist = []
		for cls in self.MODULES:
			self.modlist.append(cls(self.GROUP))

	def destroy(self):
		for cls in self.modlist:
			cls.destroy()

	def RUN(self, plr):
		for cls in self.modlist:
			cls.ST_Active(plr)


class LayoutCinema(HUDLayout):

	GROUP = "Core"
	MODULES = [Cinema]


class SceneManager:

	def __init__(self, plr):
		self.active_state = self.ST_Wait
		self.active_layout = None
		self.MENU = None

		self.start_check = True
		self.blackobj = None

		self.setControl(plr)
		self.doLoad()

	def doLoad(self):
		if self not in logic.UPDATELIST:
			logic.UPDATELIST.append(self)

	def doUpdate(self):
		scene = base.SC_HUD
		if self.MENU != None:
			return
		obj = scene.addObject(scene.objectsInactive["HUD.Loading"], scene.active_camera, 0)
		obj.applyMovement((0,0,-3), False)

	def setControl(self, plr, layout=None):
		self.control = plr
		if self.active_layout != None:
			self.active_layout.destroy()
			self.active_layout = None
		self.custom_layout = layout
		self.active_state = self.ST_Wait

	def doBlackOut(self):
		self.blackobj = base.SC_HUD.addObject("HUD.Black", base.SC_HUD.active_camera, 0)
		self.blackobj.applyMovement((0,0,-4), False)

	def doSceneSuspend(self):
		self.MENU = MenuPause()
		keymap.MOUSELOOK.center()
		base.SC_SCN.suspend()
		self.active_state = self.ST_Paused

	def doSceneResume(self):
		self.MENU.destroy()
		self.MENU = None
		keymap.MOUSELOOK.center()
		base.SC_SCN.resume()
		self.active_state = self.ST_HUD

	def ST_Wait(self):
		if self.control != None:
			plr = self.control
			if self.custom_layout == None:
				if plr.HUDLAYOUT != None:
					self.custom_layout = plr.HUDLAYOUT

			if self.custom_layout != None:
				self.active_layout = self.custom_layout()
				self.custom_layout = None

				if self.start_check == False:
					self.active_layout.RUN(plr)
				else:
					self.start_check = False

			self.active_state = self.ST_HUD

	def ST_HUD(self):
		if self.blackobj != None:
			self.blackobj.endObject()
			self.blackobj = None

		self.active_layout.RUN(self.control)

		if logic.globalDict["SCREENSHOT"]["Trigger"] == True:
			frameobj = base.SC_HUD.addObject("HUD.FreezeFrame", base.SC_HUD.active_camera, 0)
			frameobj.applyMovement((0,0,-8), True)

		if keymap.SYSTEM["ESCAPE"].tap() == True:
			self.doSceneSuspend()

	def ST_Paused(self):
		status = self.MENU.RUN()

		if status == "Quit":
			logic.endGame()

		if status == "Launcher":
			self.control.doUpdate()
			self.doBlackOut()
			self.MENU.destroy()
			self.active_state = None
			base.settings.openWorldBlend("LAUNCHER")
			#PATH = base.DATA["GAMEPATH"]
			#logic.startGame(PATH+"Launcher.blend")

		if status == "Resume" or keymap.SYSTEM["ESCAPE"].tap() == True:
			self.doSceneResume()

	def RUN(self):
		if self.active_state != None:
			self.active_state()


class MenuPause:

	ITEMS = ["Resume", "Launcher", "Quit"]
	OBJECT = "UI_Menu_Item"
	FADE = 10
	GREEN = base.mathutils.Vector([0.0, 0.8, 0.0, 1])
	GRAY = base.mathutils.Vector([0.4, 0.4, 0.4, 1])
	BLACK = base.mathutils.Vector([0.1, 0.1, 0.1, 1])

	def __init__(self):
		scene = base.SC_HUD
		owner = scene.objects["HUD.Menu"]

		self.items = []
		self.objects = {"Root":owner}

		for obj in owner.childrenRecursive:
			if "HUD.Menu." in obj.name:
				key = obj.name.replace("HUD.Menu.", "")
				self.objects[key] = obj

		self.objects["Items"].localPosition = (-5, 2.5, 0)
		self.objects["Ray"].localPosition = (0, 0, 0)

		self.objects["Cursor"].color = self.BLACK

		RES = logic.globalDict["GRAPHICS"]["Resolution"]
		self.objects["Cam"].setViewport(0, 0, RES[0], RES[1])
		self.objects["Cam"].useViewport = True

		for item in self.ITEMS:
			dict = self.addItem(self.OBJECT)
			dict["Root"]["ITEM"] = item
			dict["Root"]["TIMER"] = 0
			dict["Root"].color = self.GRAY
			dict["Text"].text = item
			dict["Text"].color = self.BLACK

	def destroy(self):
		self.objects["Cam"].useViewport = False
		for dict in self.items:
			dict["Root"].endObject()
		self.items = []

	def addItem(self, name):
		scene = base.SC_HUD
		owner = self.objects["Root"]
		point = self.objects["Items"]

		obj = scene.addObject(name, point, 0)
		obj["RAYCAST"] = False

		dict = {"Root":obj}

		for child in obj.childrenRecursive:
			key = child.name.replace(name+".", "")
			dict[key] = child

		obj.setParent(owner)
		self.items.append(dict)
		point.localPosition[1] -= 2.5

		return dict

	def RUN(self):
		click = None

		X, Y = keymap.MOUSELOOK.axis(ui=True)
		X = X*64
		Y = Y*36

		for JOYID in keymap.events.JOYBUTTONS:
			AXREF = keymap.events.JOYBUTTONS[JOYID]["Axis"]

			VALX = AXREF.get(0, {"VALUE":0})["VALUE"]
			VALY = AXREF.get(1, {"VALUE":0})["VALUE"]

			NORM = keymap.input.JoinAxis(VALX, VALY)

			X += NORM[0]*0.5
			Y -= NORM[1]*0.5

		ray = self.objects["Ray"]

		rlp = ray.localPosition.copy()
		rlp[0] += X
		rlp[1] += Y
		if rlp[0] > 32:
			rlp[0] = 32
		if rlp[0] < -32:
			rlp[0] = -32
		if rlp[1] > 18:
			rlp[1] = 18
		if rlp[1] < -18:
			rlp[1] = -18

		ray.localPosition[0] = rlp[0]
		ray.localPosition[1] = rlp[1]

		rayOBJ = ray.rayCastTo(self.objects["Cursor"], 100, "RAYCAST")

		if rayOBJ != None:
			rayOBJ["RAYCAST"] = True

		for dict in self.items:
			obj = dict["Root"]
			txt = dict["Text"]

			if obj["RAYCAST"] == True:
				if obj["TIMER"] < self.FADE:
					obj["TIMER"] += 1

				if keymap.SYSTEM["LEFTCLICK"].tap() == True:
					click = obj["ITEM"]

			elif obj["TIMER"] > 0:
				obj["TIMER"] -= 1

			obj.color = self.GRAY.lerp(self.GREEN, obj["TIMER"]/self.FADE)

			obj["RAYCAST"] = False

		return click






