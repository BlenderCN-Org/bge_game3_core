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

## HUD ##


from bge import logic

from mathutils import Vector

from . import keymap, base, settings, config, world, COREBLENDS


def START(cont):
	owner = cont.owner

	base.SC_HUD = owner.scene

	base.SC_HUD.post_draw.append(settings.SCREENSHOT)
	if settings.SCREENSHOT in base.SC_SCN.post_draw:
		base.SC_SCN.post_draw.remove(settings.SCREENSHOT)

	print("Loading HUD...")
	base.LEVEL["HUDData"] = {}

	libblend = base.DATA["GAMEPATH"]+config.LIBRARY_PATH+"\\Game Assets HUD.blend"

	logic.LibLoad(libblend, "Scene", load_actions=True, verbose=False, load_scripts=True)

	logic.HUDCLASS = SceneManager()
	#logic.HUDCLASS.doBlackOut(True, que=True)


def RUN(cont):
	if logic.HUDCLASS != None:
		#try:
		logic.HUDCLASS.RUN()
		#except Exception as ex:
		#	logic.HUDCLASS.setControl(None, None)
		#	logic.HUDCLASS = None
		#	print("FATAL RUNTIME ERROR:", cont.owner.name)
		#	print("\t", ex)


def SetLayout(plr=None, layout=None):
	if base.SC_HUD == None or logic.HUDCLASS == None:
		return

	logic.HUDCLASS.setControl(plr, layout)

def SetBlackScreen(mode=True):
	if base.SC_HUD == None or logic.HUDCLASS == None:
		return

	logic.HUDCLASS.doBlackOut(mode, que=True)


class CoreHUD(base.CoreObject):

	UPDATE = False
	OBJECT = "None"

	def __init__(self, prefix):
		scene = base.SC_HUD
		owner = scene.addObject(prefix+self.OBJECT, scene.objects["HUD.START"], 0)

		self.objects = {"Root":owner}

		self.data = self.defaultData()

		if self.OBJECT not in base.LEVEL["HUDData"]:
			base.LEVEL["HUDData"][self.OBJECT] = self.data
		else:
			self.data = base.LEVEL["HUDData"][self.OBJECT]

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

	def defaultData(self):
		dict = {"Target":(0,0,0), "Map":None, "Scene":None}
		return dict

	def ST_Startup(self):
		oldcam = base.SC_HUD.active_camera
		base.SC_HUD.active_camera = self.objects["Cam"]
		RES = logic.globalDict["GRAPHICS"]["Resolution"]
		self.objects["Cam"].useViewport = True
		self.objects["Cam"].setViewport(0, 0, RES[0], RES[1])
		base.SC_HUD.active_camera = oldcam

	def destroy(self):
		self.objects["Cam"].useViewport = False
		self.objects["Root"].endObject()
		self.objects["Root"] = None

	#def getDoorTarget(self, map):
	#	for obj in base.SC_SCN.objects:
	#		if "MAP" in obj:

	def ST_Active(self, plr):
		root = plr.objects["Root"]

		cp_comp = self.objects["Direction"]
		cp_dist = self.objects["Distance"]

		target = self.data["Target"]

		vd, vg, vl = root.getVectTo(target)

		look = base.SC_SCN.active_camera.getAxisVect((0,0,-1))
		look[2] = 0
		vg[2] = 0
		rdif = look.rotation_difference(vg)
		rdif = rdif.to_euler()
		rdif[0] = 0
		rdif[1] = 0
		rdif.to_matrix()

		if vg.length < 0.1:
			rdif = self.createMatrix()

		cp_comp.localOrientation = rdif

		if vd < 300:
			vd = (1-(vd/300))**3
			cp_dist.color[1] = vd
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

	def ST_Active(self, plr):
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
		plr.data["HUD"]["Color"] = (0, 0, 0, 0.5)

		if pos == None:
			self.objects["Target"].localPosition = (0, 0, 64)
		else:
			self.objects["Target"].localPosition = ((pos[0]-0.5)*64, (0.5-pos[1])*36, 0)

		self.objects["Target"].color = color


class MousePos(CoreHUD):

	OBJECT = "MousePos"

	def ST_Startup(self):
		self.boot_timer = 0

	def ST_Active(self, plr):

		pos = plr.data["HUD"]["Target"]

		if pos == None:
			self.objects["Root"].setVisible(False, True)
		else:
			self.objects["Root"].setVisible(True, True)

			pos = self.createVector(vec=(pos[0], pos[1], 0))*12

			self.objects["Cursor"].localPosition = pos.copy()
			self.objects["Line"].localScale = (1,pos.length,1)

			if pos.length < 0.01:
				self.objects["Line"].color = (0,1,0,0)
			else:
				self.objects["Line"].alignAxisToVect(pos, 1, 1.0)
				self.objects["Line"].alignAxisToVect((0,0,1), 2, 1.0)

				if pos.length < 1:
					A = (pos.length*1.01)-0.01
					self.objects["Line"].color = (0,1,0,A)
				else:
					self.objects["Line"].color = (0,1,0,1)


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
		xpos = offset*stat

		if stat < 0.1:
			txt.color = (1,0,0,1)
		elif stat > 1:
			xpos = offset
			txt.color = (1,0,1,1)
		else:
			txt.color = (0,1,0,0.5)

		bar.color[0] = stat
		txt.localPosition[0] = xpos
		txt.text = str(int(round(value, 0)))


class Weapons(CoreHUD):

	OBJECT = "Weapons"

	def ST_Startup(self):
		self.weaptype = ""

	def ST_Active(self, plr):
		weap = plr.data["WPDATA"]

		mode = self.objects["Mode"]
		wpid = self.objects["ID"]
		stat = self.objects["Text"]

		type = weap["CURRENT"]+str(weap["ACTIVE"]!="NONE")

		if self.weaptype != type:
			self.weaptype = type
			if "NONE" in type:
				self.objects["Root"].setVisible(False, True)
			else:
				self.objects["Root"].setVisible(True, True)
			if "MELEE" in type:
				mode.worldOrientation = self.createMatrix(mirror="XZ")
			if "RANGED" in type:
				mode.worldOrientation = self.createMatrix()

			if weap["ACTIVE"] == "NONE":
				mode.color = (0.4, 0.4, 0.4, 0.5)
				stat.color = (0.4, 0.4, 0.4, 0.5)
				wpid.color = (0.4, 0.4, 0.4, 0.5)
			else:
				mode.color = (0, 0, 0, 0.5)
				stat.color = (0, 1, 0, 0.5)
				wpid.color = (0, 1, 0, 0.5)

		if weap["CURRENT"] != "NONE":
			wheel = weap["WHEEL"][weap["CURRENT"]]
			ID = wheel["ID"]
			SLOT = wheel["LIST"][ID]

			wpid.text = str(ID)
			stat.text = str(plr.cls_dict[SLOT].data["HUD"]["Text"])

		else:
			wpid.text = "000"
			stat.text = "000"

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

		for slot in plr.cls_dict:
			dict = plr.cls_dict[slot].dict

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

			if dict in plr.data["INVENTORY"]:
				pos = plr.data["INVENTORY"].index(dict)
			elif dict in plr.data["WEAPONS"]:
				pos = plr.data["WEAPONS"].index(dict)+len(plr.data["INVENTORY"])+0.25

			obj["Icon"].localPosition[1] = pos*-2
			obj["Stat"].localScale[0] = 1-(data["HUD"]["Stat"]/100)
			#obj["Stat"].color[1] = 1-(data["HUD"]["Stat"]/100)
			obj["Text"].text = str(data["HUD"]["Text"])

			#obj["Icon"].worldOrientation = obj["Icon"].scene.active_camera.worldOrientation

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

		statobj.localPosition = (1,0,1)
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
		vec = root.localLinearVelocity*self.createVector(vec=refY)
		speed = abs(vec)*2.237
		self.objects["Text"].text = str(round(speed))
		self.objects["Units"].text = "Mph"
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

		glbZ = -plr.gravity
		angX = 0
		angY = 90

		if glbZ.length >= 0.1:

			## Roll ##
			refX = plr.data["HUD"].get("Side", (1,0,0))
			angX = root.getAxisVect(refX).angle(glbZ)
			angX = self.toDeg(angX)
			angX = (angX-90)*0.167

			## Pitch ##
			refY = plr.data["HUD"].get("Forward", (0,1,0))
			angY = root.getAxisVect(refY).angle(glbZ)
			angY = self.toDeg(angY)

		self.objects["Roll"].localOrientation = self.createMatrix(rot=[0,0,angX], deg=True)
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
	MODULES = []

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

	def __init__(self):
		self.active_state = self.ST_Wait
		self.active_layout = None
		self.custom_layout = None
		self.control = None
		self.firstrun = True
		self.blackobj = None
		self.MENU = None

	def setControl(self, plr, layout):
		self.control = plr
		self.custom_layout = layout
		self.active_state = self.ST_Wait

	def doBlackOut(self, add=True, que=False):
		state = (self.blackobj not in [None, "QUE"])

		if add == True:
			if state == False:
				if que == True:
					self.blackobj = "QUE"
				else:
					print("HUD: LoadScreen")
					self.blackobj = base.SC_HUD.addObject("HUD.Black", base.SC_HUD.active_camera, 0)
					self.blackobj.applyMovement((0,0,-4), False)

		elif state == True:
			self.blackobj.endObject()
			self.blackobj = None

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
		if self.active_layout != None:
			self.active_layout.destroy()
			self.active_layout = None

		if self.control == None:
			self.active_state = self.ST_HUD
			return

		plr = self.control
		if self.custom_layout == None:
			if plr.HUDLAYOUT != None:
				self.custom_layout = plr.HUDLAYOUT

		if self.custom_layout != None:
			self.active_layout = self.custom_layout()
			self.custom_layout = None

			if self.firstrun == True:
				self.firstrun = False
			else:
				self.active_layout.RUN(plr)

		self.active_state = self.ST_HUD

	def ST_HUD(self):

		if self.active_layout != None:
			self.doBlackOut(False)
			self.active_layout.RUN(self.control)

		if keymap.SYSTEM["ESCAPE"].tap() == True:
			self.doSceneSuspend()

	def ST_Paused(self):
		status = self.MENU.RUN()

		if status == "Quit":
			logic.endGame()

		if status == "Keymap":
			self.doBlackOut()
			self.MENU.destroy()
			self.active_state = None
			world.openBlend("KEYMAP")

		if status == "Launcher":
			self.doBlackOut()
			self.MENU.destroy()
			self.active_state = None
			world.openBlend("LAUNCHER")

		if status == "Resume" or keymap.SYSTEM["ESCAPE"].tap() == True:
			self.doSceneResume()

	def RUN(self):
		if self.blackobj == "QUE":
			self.doBlackOut()
		if self.active_state != None:
			self.active_state()

		if logic.globalDict["SCREENSHOT"]["Trigger"] == True:
			frameobj = base.SC_HUD.addObject("HUD.FreezeFrame", base.SC_HUD.active_camera, 0)
			frameobj.applyMovement((0,0,-8), True)
			if keymap.SYSTEM["SHIFT"].checkModifiers() != True and "HUD.Watermark" in base.SC_HUD.objectsInactive:
				frameobj = base.SC_HUD.addObject("HUD.Watermark", base.SC_HUD.active_camera, 5)
				frameobj.applyMovement((0,0,-8), True)


class MenuPause:

	ITEMS = ["Resume", "Keymap", "Launcher", "Quit"]
	OBJECT = "UI_Menu_Item"
	OFFSET = 2.5
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

		offset = (self.OFFSET*(len(self.ITEMS)/2))-(self.OFFSET/2)

		self.objects["Items"].localPosition = (-5, offset, 0)
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
		point.localPosition[1] -= self.OFFSET

		return dict

	def RUN(self):
		click = None

		X, Y = keymap.MOUSELOOK.axis(ui=True)
		X *= 64
		Y *= 36

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






