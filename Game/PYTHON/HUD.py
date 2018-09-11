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

#subt = [{"NAME":"Name A", "TIME":100, "COLOR":(0,1,1),
#		"LINE":""},
#]

SPAWN = None
CONTROL = None
SUBTITLE = [None, 0, 0, []]
COMPASS = None
CINEMA = None

logic.HUDCLASS = None

if "CURRENT" in logic.globalDict:
	logic.addScene("HUD", 1)


def START(cont):
	owner = cont.owner
	scene = owner.scene

	base.SC_HUD = scene

	scene.post_draw.append(base.settings.SCREENSHOT)

	print("Loading HUD...")

	logic.LibLoad( base.DATA["GAMEPATH"]+"CONTENT\\Game Assets HUD.blend", "Scene", load_actions=True, verbose=False, load_scripts=True, async=False)

	black = scene.addObject(scene.objectsInactive["HUD.Black"], scene.active_camera, 0)
	black.applyMovement((0,0,-4), False)

	RES = logic.globalDict["GRAPHICS"]["Resolution"]
	scene.objects["HUD.Cam.Compass"].setViewport(0, 0, RES[0], RES[1])
	scene.objects["HUD.Cam.Compass"].useViewport = True


def RUN(cont):
	scene = cont.owner.scene
	global SPAWN, CONTROL, SUBTITLE, COMPASS, CINEMA

	if SPAWN != None:
		logic.HUDCLASS = SPAWN(CONTROL)
		SPAWN = None
		return

	if logic.HUDCLASS != None and logic.PLAYERCLASS != None:
		#try:
		logic.HUDCLASS.RUN()
		#except Exception as ex:
		#	print("FATAL RUNTIME ERROR: HUD")
		#	print("	", ex)
		#	cont.owner.endObject()

	if CINEMA == False:
		base.SC_HUD.active_camera = base.SC_HUD.objects["HUD.Main.Cam"]
		base.SC_HUD.objects["HUD.Cam.Compass"].useViewport = True
		CINEMA = None
	elif CINEMA == True:
		base.SC_HUD.active_camera = base.SC_HUD.objects["HUD.Cinema.Cam"]
		base.SC_HUD.objects["HUD.Cam.Compass"].useViewport = False
		CINEMA = None

	if base.SC_SCN.suspended == True:
		return

	## COMPASS ##
	cp_comp = scene.objects["HUD.Compass.Direction"]
	cp_dist = scene.objects["HUD.Compass.Distance"]

	if COMPASS == None:
		target = [0, 10000, 0]
	else:
		target = COMPASS

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

	## MANAGE SUBTITLES ##
	fade = False
	if SUBTITLE[0] != None:
		OBJ = scene.objects["HUD.Main.Subtitles"]
		CUR = SUBTITLE[0][SUBTITLE[2]]
		if SUBTITLE[1] == 0:
			name = scene.addObject("Subtitle", OBJ, 0)
			name.color = (0, 0, 0, 0.5)
			name.children["Subtitle.NameText"].color = (CUR["COLOR"][0], CUR["COLOR"][1], CUR["COLOR"][2], 0)
			name.children["Subtitle.NameText"].text = CUR["NAME"]
			name.children["Subtitle.LineText"].color = (0.8, 0.8, 0.8, 0)
			name.children["Subtitle.LineText"].text = CUR["LINE"]
			name.children["Subtitle.Line"].localScale[1] = len(CUR["LINE"].split("\n"))
			SUBTITLE[3].append(name)
		if len(SUBTITLE[3]) >= 2:
			fade = True
		SUBTITLE[1] += 1
		if SUBTITLE[1] > abs(CUR["TIME"])+30:
			SUBTITLE[1] = 0
			SUBTITLE[2] += 1
			if SUBTITLE[2] >= len(SUBTITLE[0]):
				SUBTITLE[0] = None
				SUBTITLE[2] = 0
		elif SUBTITLE[1] <= 30:
			alpha = SUBTITLE[1]/30
			SUBTITLE[3][-1].color[3] = alpha*0.5
			SUBTITLE[3][-1].children["Subtitle.Line"].color[3] = alpha*0.5
			SUBTITLE[3][-1].children["Subtitle.NameText"].color[3] = alpha
			SUBTITLE[3][-1].children["Subtitle.LineText"].color[3] = alpha
			for box in SUBTITLE[3]:
				hgt = 1.5+(SUBTITLE[3][-1].children["Subtitle.Line"].localScale[1])
				box.localPosition[1] += hgt*(1/30)

	elif len(SUBTITLE[3]) >= 1:
		SUBTITLE[1] += 1
		fade = True
		if SUBTITLE[1] > 30:
			SUBTITLE[1] = 0

	if fade == True:
		if SUBTITLE[1] == 30:
			SUBTITLE[3].pop(0).endObject()
		elif SUBTITLE[1] < 30:
			alpha = 1-(SUBTITLE[1]/30)
			SUBTITLE[3][0].color[3] = alpha*0.5
			SUBTITLE[3][0].children["Subtitle.Line"].color[3] = alpha*0.5
			SUBTITLE[3][0].children["Subtitle.NameText"].color[3] = alpha
			SUBTITLE[3][0].children["Subtitle.LineText"].color[3] = alpha


class CoreHUD(base.CoreObject):

	MESH = "CoreHUD"

	def __init__(self, control):
		scene = base.SC_HUD

		self.addobj = scene.objects["HUD.START"]

		obj = scene.addObject(scene.objectsInactive[self.MESH], self.addobj, 0)

		self.objects = {"Root":obj}

		self.itemdict = {}
		self.weaptype = ""

		self.active_state = self.ST_HUD

		self.findObjects(obj)
		self.doLoad()
		self.ST_Startup()

		self.setControl(control)

	def ST_Startup(self):
		self.boot_timer = 0
		prf = logic.globalDict["CURRENT"]["Profile"]
		if "_" in prf:
			prf = "None"
		self.objects["Profile"].text = prf
		self.objects["RayText"].text = "."
		self.objects["Target"].localPosition = (0, 0, 64)
		self.objects["Items"].localPosition = (-31, 8, 0)

	def doLoad(self):
		if self not in logic.UPDATELIST:
			logic.UPDATELIST.append(self)

	def doUpdate(self):
		scene = base.SC_HUD
		obj = scene.addObject(scene.objectsInactive["HUD.Loading"], scene.active_camera, 0)
		obj.applyMovement((0,0,-3), False)

	def destroy(self):
		self.objects["Root"].endObject()
		self.objects["Root"] = None

	def setControl(self, control):
		self.control = control
		self.objects["Object"].text = control.NAME
		self.objects["Object"].worldPosition[0] = 32-((len(control.NAME)*0.42)+1)

		for slot in self.itemdict:
			obj = self.itemdict[slot]

			obj["Icon"].endObject()
			if obj["Slot"] != None:
				obj["Slot"].endObject()

		self.itemdict = {}

	def setSubtitle(self, subt):
		for obj in SUBTITLE[3]:
			obj.endObject()

		SUBTITLE[0] = subt
		SUBTITLE[1] = 0
		SUBTITLE[2] = 0
		SUBTITLE[3] = []

	def setTargetPos(self, pos, color):
		if pos == None:
			x = 0
			y = 0
			z = 64
		else:
			x = (pos[0]-0.5)*2
			y = (0.5-pos[1])*2
			z = 0

		self.objects["Target"].localPosition = (x*32, y*18, z)
		self.objects["Target"].color = color

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

	def setWeaponType(self, weap):
		mode = self.objects["WeapMode"]
		wpid = self.objects["WeapID"]
		stat = self.objects["WeapStat"]

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

		stat.text = str(self.control.cls_dict[SLOT].data["HUD"]["Stat"])
		stat.worldPosition[0] = (len(stat.text)*-0.59)-2

	def refreshItems(self):
		plr = self.control
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

	def ST_HUD(self):
		plr = self.control

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

		self.objects["RayText"].text = text

		plr.data["HUD"]["Text"] = ""

		self.setTargetPos(pos, color)
		self.setWeaponType(plr.data["WPDATA"])

		self.setStat("Health", plr.data["HEALTH"], 15)
		self.setStat("Energy", plr.data["ENERGY"], 14.1)

		self.refreshItems()

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
			PATH = base.DATA["GAMEPATH"]
			logic.startGame(PATH+"Launcher.blend")
			black = base.SC_HUD.addObject(base.SC_HUD.objectsInactive["HUD.Black"], base.SC_HUD.active_camera, 0)
			black.applyMovement((0,0,-2), False)

			self.doSceneResume()

		if status == "Resume" or keymap.SYSTEM["ESCAPE"].tap() == True:
			self.doSceneResume()

	def RUN(self):
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

		X, Y = logic.mouse.position

		for JOYID in keymap.events.JOYBUTTONS:
			ZONE = 0.2
			AXREF = keymap.events.JOYBUTTONS[JOYID]["Axis"]

			VALX = AXREF.get(0, {"VALUE":0})["VALUE"]
			ABSX = (abs(VALX)-ZONE)*(1/(1-ZONE))

			if VALX >= ZONE:
				X += ABSX*0.01
			elif VALX <= -ZONE:
				X += ABSX*-0.01

			VALY = AXREF.get(1, {"VALUE":0})["VALUE"]
			ABSY = (abs(VALY)-ZONE)*(1/(1-ZONE))

			if VALY >= ZONE:
				Y += ABSY*0.01
			elif VALY <= -ZONE:
				Y += ABSY*-0.01

		logic.mouse.position = (X, Y)

		X, Y = logic.mouse.position

		ray = self.objects["Ray"]

		ray.localPosition[0] = (X-0.5)*64
		ray.localPosition[1] = (0.5-Y)*36

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






