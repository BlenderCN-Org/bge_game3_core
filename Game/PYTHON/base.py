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

## GAME CORE ##

import sys
for i in sys.path:
	print("PATH:", i)

import mathutils
import math

from bge import logic

import PYTHON.keymap as keymap
import PYTHON.settings as settings


SC_SCN = logic.getCurrentScene()
SC_HUD = None
SC_CAM = SC_SCN.active_camera

if "CURRENT" not in logic.globalDict:
	SC_CAM.near = 0.1
	SC_CAM.far = 0.2
	settings.render.setBackgroundColor((0,0,0,1))
	PATH = logic.expandPath("//../")
	logic.startGame(PATH+"Launcher.blend")

CURRENT = logic.globalDict["CURRENT"]

CUR_LVL = CURRENT["Level"]+SC_SCN.name
CUR_PRF = CURRENT["Profile"]
CUR_PLR = CURRENT["Player"]

PROFILE = logic.globalDict["PROFILES"][CUR_PRF]

if CUR_LVL not in PROFILE["LVLData"]:
	print("Initializing Level Data...")
	PROFILE["LVLData"][CUR_LVL] = {"SPAWN":[], "DROP":[], "CLIP":-100, "PLAYER":{}}

LEVEL = PROFILE["LVLData"][CUR_LVL]

DATA = logic.globalDict["DATA"]

logic.UPDATELIST = []

settings.SETGFX(logic.globalDict["GRAPHICS"])


def LOAD(owner):
	global CURRENT, LEVEL, DATA, PROFILE

	scene = owner.scene

	## Load Key Binds ##
	profile = CURRENT["Profile"]
	if "_" in profile:
		profile = "Base"

	keymap.input.LoadBinds(keymap.BINDS, DATA["GAMEPATH"], profile)

	mouse_settings = PROFILE["Settings"].get("Mouse", None)
	if mouse_settings != None:
		keymap.MOUSELOOK.updateSpeed(mouse_settings["Speed"], mouse_settings["Smoothing"])
	else:
		PROFILE["Settings"]["Mouse"] = {"Speed":keymap.MOUSELOOK.input, "Smoothing":keymap.MOUSELOOK.smoothing}

	## Ground Detector ##
	for obj in scene.objects:
		gnd = obj.get("GROUND", None)
		if gnd == False:
			del obj["GROUND"]
		elif obj.getPhysicsId() != 0:
			obj["GROUND"] = True

	## Spawn New Objects ##
	cleanup = []

	for obj in scene.objects:
		split = obj.name.split(".")
		name = None

		if split[0] == "Spawn" and len(split) > 1:
			if split[1] != "Player":
				name = obj.get("OBJECT", split[1])

		if name != None:
			cleanup.append(obj)

			if obj.get("SPAWN", True) == True and obj.name not in LEVEL["SPAWN"]:
				if name in scene.objectsInactive:
					newobj = scene.addObject(name, obj, 0)
					for prop in obj.getPropertyNames():
						if prop not in ["SPAWN", "OBJECT", "DICT"]:
							newobj[prop] = obj[prop]
					newobj["DICT"] = {"Object":name, "Data":None, "Add":obj.name}
					print("SPAWNED:", name)
				else:
					print("SPAWN ERROR: Object '"+name+"' does not exist")
			else:
				print("NOT SPAWNED:", name)

	for obj in cleanup:
		obj.endObject()

	## Load Cyberspace Objects ##
	for drop in LEVEL["DROP"]:
		newobj = scene.addObject(drop["Object"], owner, 0)
		newobj.worldPosition = drop["Data"]["POS"]
		newobj.worldOrientation = drop["Data"]["ORI"]
		if "SCL" in drop["Data"]:
			newobj.worldScale = drop["Data"]["SCL"]
		newobj["DICT"] = drop
		print("CYBERSPACE:", drop["Object"])

	LEVEL["DROP"] = []

	if DATA["Portal"]["Vehicle"] != None:
		dict = DATA["Portal"]["Vehicle"]
		portal = scene.addObject(dict["Object"], owner, 0)
		portal.worldPosition = LEVEL["PLAYER"]["POS"]
		portal.worldOrientation = LEVEL["PLAYER"]["ORI"]
		portal["DICT"] = dict
		return portal

	return None


def RUN(cont):
	owner = cont.owner
	#try:
	owner["Class"].RUN()
	#except Exception as ex:
	#	print("FATAL RUNTIME ERROR:", owner.name)
	#	print("	", ex)
	#	if owner.scene.active_camera in owner.childrenRecursive:
	#		owner.scene.active_camera = SC_CAM
	#	owner.endObject()

class CoreObject:

	NAME = "Object"
	UPDATE = True
	GHOST = False
	LOCK = ""
	PORTAL = False
	ANIMOBJ = None

	def __init__(self):
		owner = logic.getCurrentController().owner

		owner["Class"] = self

		owner["RAYCAST"] = owner.get("RAYCAST", None)
		owner["RAYNAME"] = self.NAME

		self.objects = {"Root":owner}

		self.data = self.defaultData()

		self.active_pre = []
		self.active_state = self.ST_Disabled
		self.active_post = []

		self.checkGhost(owner)
		self.findObjects(owner)
		self.doLoad()

		self.ST_Startup()

	def findObjects(self, obj):
		dict = self.objects
		group = []
		list = []

		for child in obj.childrenRecursive:
			self.checkGhost(child)
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

		if "INV" not in self.objects:
			self.objects["INV"] = {}

	def createVector(self, size=3, fill=0, vec=None):
		if vec == None:
			vec = [fill]*int(size)
		return mathutils.Vector(vec)

	def createMatrix(self, rot=None, deg=True, mirror=""):
		if rot != None:
			if deg == True:
				rot = [math.radians(rot[0]), math.radians(rot[1]), math.radians(rot[2])]
			euler = mathutils.Euler(rot)
			return euler.to_matrix()

		mat = mathutils.Matrix.Identity(3)

		if "X" in mirror:
			mat[0][0] = -1
		if "Y" in mirror:
			mat[1][1] = -1
		if "Z" in mirror:
			mat[2][2] = -1

		return mat

	def toDeg(self, rad):
		return math.degrees(rad)

	def vecTuple(self, POS):
		NEWPOS = list(POS)
		return NEWPOS

	def matTuple(self, ORI):
		NEWORI = [list(ORI[0]), list(ORI[1]), list(ORI[2])]
		return NEWORI

	def addCollisionCallBack(self, obj=None):
		if obj == None:
			obj = self.objects["Root"]

		self.clearCollisionList()
		obj.collisionCallbacks = [self.COLCB]

		self.active_post.append(self.clearCollisionList)

	def clearCollisionList(self):
		self.collisionList = []

	def COLCB(self, OBJ):
		if "COLLIDE" in OBJ:
			if self not in OBJ["COLLIDE"]:
				OBJ["COLLIDE"].append(self)

		if OBJ not in self.collisionList:
			self.collisionList.append(OBJ)

	def checkGhost(self, obj):
		if obj.getPhysicsId() != 0 and self.GHOST == False:
			obj["GROUND"] = True

	def saveWorldPos(self):
		obj = self.objects["Root"]
		self.data["POS"] = self.vecTuple(obj.worldPosition)
		self.data["ORI"] = self.matTuple(obj.worldOrientation)
		self.data["SCL"] = self.vecTuple(obj.worldScale)

	def defaultData(self):
		return {}

	def doLoad(self):
		owner = self.objects["Root"]

		if self.UPDATE == False:
			return

		if owner["DICT"]["Data"] == None:
			owner["DICT"]["Data"] = self.data
			self.data["ACTIVE_STATE"] = self.active_state.__name__
			self.saveWorldPos()
		else:
			self.data = owner["DICT"]["Data"]
			self.active_state = getattr(self, self.data["ACTIVE_STATE"])

		global LEVEL
		if "Add" in owner["DICT"]:
			LEVEL["SPAWN"].append(owner["DICT"]["Add"])
			del owner["DICT"]["Add"]

		if self not in logic.UPDATELIST:
			logic.UPDATELIST.append(self)

	def doUpdate(self):
		owner = self.objects["Root"]

		self.saveWorldPos()

		global LEVEL
		if self.UPDATE == True and owner["DICT"] not in LEVEL["DROP"]:
			LEVEL["DROP"].append(owner["DICT"])

	def teleportTo(self, pos=None, ori=None, vel=False):
		owner = self.objects["Root"]

		if pos != None:
			owner.worldPosition = pos
		if ori != None:
			owner.worldOrientation = ori
		if vel == False:
			owner.worldLinearVelocity = (0,0,0)

	def hideObject(self):
		self.objects["Root"].setVisible(False, True)

	def doAnim(self, OBJECT=None, NAME="NONE", FRAME=(0, 60), LAYER=0, PRIORITY=0, MODE="PLAY", BLEND=0, KEY=False, STOP=False, CHECK=False, SET=None):

		if type(OBJECT) is str:
			if OBJECT not in self.objects:
				OBJECT = None
			else:
				OBJECT = self.objects[OBJECT]

		if OBJECT == None:
			if self.ANIMOBJ != None:
				OBJECT = self.ANIMOBJ
			else:
				OBJECT = self.objects["Root"]

		if SET != None:
			OBJECT.setActionFrame(SET, LAYER)
			return

		if CHECK == True:
			ACTCHK = OBJECT.isPlayingAction(LAYER)
			return ACTCHK

		if STOP == True:
			OBJECT.stopAction(LAYER)
			return

		if NAME == "NONE":
			NAME = OBJECT.name
		if NAME == None:
			return

		SPEED = 1
		LYRWGHT = 0
		IPO_FLG = 0

		if MODE == "PLAY":
			PLAYTYPE = logic.KX_ACTION_MODE_PLAY

		elif MODE == "LOOP":
			PLAYTYPE = logic.KX_ACTION_MODE_LOOP

		BLENDTYPE = logic.KX_ACTION_BLEND_BLEND

		OBJECT.playAction(NAME, FRAME[0], FRAME[1], LAYER, PRIORITY, BLEND, PLAYTYPE, LYRWGHT, IPO_FLG, SPEED, BLENDTYPE)
		if KEY == True:
			OBJECT.reinstancePhysicsMesh()

	def checkStability(self, align=False, offset=1.0):
		obj = self.objects["Root"]

		rayto = obj.worldPosition.copy()
		rayto[2] += 1

		down, pnt, nrm = obj.rayCast(rayto, None, -20000, "GROUND", 1, 1, 0)

		if down == None:
			up, pnt, nrm = obj.rayCast(rayto, None, 10000, "GROUND", 1, 1, 0)
			if up != None:
				obj.worldPosition[2] = pnt[2]+offset
				if align == True:
					obj.alignAxisToVect(nrm, 2, 1.0)
			else: #if obj.getPhysicsId() != 0:
				obj.applyForce((0,0,-obj.scene.gravity[2]*obj.mass), False)

	def checkClicked(self, obj=None):
		if obj == None:
			obj = self.objects["Root"]

		if obj["RAYCAST"] != None:
			if keymap.BINDS["ACTIVATE"].tap() == True:
				return True
		return False

	def clearRayProps(self):
		self.objects["Root"]["RAYCAST"] = None

	## INIT STATE ##
	def ST_Startup(self):
		pass

	## STATE DISABLED ##
	def ST_Disabled(self):
		if self.checkClicked() == True:
			self.ST_Active_Set()

	def ST_Disabled_Set(self):
		self.active_state = self.ST_Disabled

	## STATE ACTIVE ##
	def ST_Active(self):
		if self.checkClicked() == True:
			self.ST_Disabled_Set()

	def ST_Active_Set(self):
		self.active_state = self.ST_Active

	## RUN ##
	def runPre(self):
		for run in self.active_pre:
			run()

	def runStates(self):
		self.active_state()
		self.data["ACTIVE_STATE"] = self.active_state.__name__

	def runPost(self):
		for run in self.active_post:
			run()

	def RUN(self):
		self.runPre()
		self.runStates()
		self.runPost()
		self.clearRayProps()


class CoreAdvanced(CoreObject):

	WP_TYPE = "RANGED"
	INVENTORY = {}
	SLOTS = {}

	def doScreenshot(self):
		settings.triggerPrintScreen()

	def loadInventory(self, owner):
		scene = owner.scene

		wpfb = self.WeaponFallback(self)
		self.cls_dict = {"__Fallback_WP":wpfb}
		self.active_weapon = None
		self.active_pre.append(wpfb.RUN)

		items = self.buildInventory()

		for dict in items:
			obj = scene.addObject(dict["Object"], owner, 0)
			obj["DICT"] = dict
			obj["RAYCAST"] = self

		for dict in self.data["WEAPONS"]:
			obj = scene.addObject(dict["Object"], owner, 0)
			obj["DICT"] = dict
			obj["RAYCAST"] = self

		if self.data["WPDATA"]["ACTIVE"] == "ACTIVE":
			type = self.data["WPDATA"]["CURRENT"]
			if self.data["WPDATA"]["WHEEL"][type]["ID"] == -1:
				self.active_weapon = wpfb

		char = self.objects.get("Character", None)
		if char == None:
			return

		char["WP_ACTIVE"] = ""
		char["WP_TIMER"] = ""
		char["WP_CLASS"] = ""
		char.addDebugProperty("WP_ACTIVE", True)
		char.addDebugProperty("WP_TIMER", True)
		char.addDebugProperty("WP_CLASS", True)

	def buildInventory(self):
		if "INVENTORY" in self.data:
			return self.data["INVENTORY"]

		self.data["KEYRING"] = [""]

		self.data["WPDATA"] = {"ACTIVE":"NONE", "CURRENT":self.WP_TYPE, "TIMER":0, "WHEEL":{}}

		for type in ["MELEE", "RANGED"]:
			self.data["WPDATA"]["WHEEL"][type] = {"ID":-1, "LIST":[]}

		defaults = self.SLOTS
		self.data["SLOTS"] = {}

		for key in defaults:
			slot = defaults[key]
			new = "SLOT_"+key
			self.data["SLOTS"][slot] = new

		self.data["INVENTORY"] = []
		self.data["INVSLOT"] = {}
		self.data["WEAPONS"] = []
		self.data["WEAPSLOT"] = {}

		defaults = self.INVENTORY
		items = []

		for slot in defaults:
			dict = {"Object":defaults[slot], "Data":None, "Equiped":slot}
			items.append(dict)

		return items

	def weaponManager(self):
		weap = self.data["WPDATA"]

		## MODE SWITCH ##
		if keymap.BINDS["WP_MODE"].tap() == True:
			if weap["CURRENT"] == "MELEE":
				weap["CURRENT"] = "RANGED"
			elif weap["CURRENT"] == "RANGED":
				weap["CURRENT"] = "MELEE"

		dict = weap["WHEEL"][weap["CURRENT"]]

		## WEAPON SELECT ##
		if keymap.BINDS["WP_UP"].tap() == True and weap["ACTIVE"] != "SWITCH":
			dict["ID"] += 1
			weap["TIMER"] = 0
			if dict["ID"] == len(dict["LIST"]):
				dict["ID"] = -1

		elif keymap.BINDS["WP_DOWN"].tap() == True and weap["ACTIVE"] != "SWITCH":
			dict["ID"] -= 1
			weap["TIMER"] = 0
			if dict["ID"] == -2:
				dict["ID"] = len(dict["LIST"])-1

		if dict["ID"] >= len(dict["LIST"]):
			dict["ID"] = len(dict["LIST"])-1

		## STATE MANAGER ##
		if weap["ACTIVE"] == "ACTIVE":
			if self.active_weapon != None:

				if dict["ID"] == -1:
					slot = "__Fallback_WP"
				else:
					slot = dict["LIST"][dict["ID"]]

				if self.active_weapon != self.cls_dict[slot]:
					if weap["TIMER"] == 10:
						check = self.active_weapon.doSheath()
						if check == True:
							weap["TIMER"] = 0
							weap["ACTIVE"] = "SWITCH"

					else:
						weap["TIMER"] += 1

				## STATE PASSIVE ##
				if keymap.BINDS["SHEATH"].tap() == True:
					check = self.active_weapon.doSheath()
					if check == True:
						weap["TIMER"] = 0
						weap["ACTIVE"] = "NONE"

			else:
				weap["ACTIVE"] = "NONE"

		elif weap["ACTIVE"] == "SWITCH":
			if self.active_weapon == None:

				if dict["ID"] == -1:
					slot = "__Fallback_WP"
				else:
					slot = dict["LIST"][dict["ID"]]

				self.active_weapon = self.cls_dict[slot]

				check = self.active_weapon.doDraw()
				if check == True:
					weap["TIMER"] = 0
					weap["ACTIVE"] = "ACTIVE"

		elif weap["ACTIVE"] == "NONE":
			if self.active_weapon == None:

				## STATE ACTIVE ##
				if keymap.BINDS["SHEATH"].tap() == True:
					weap["TIMER"] = 0
					weap["ACTIVE"] = "SWITCH"

			else:
				weap["TIMER"] = 0
				self.active_weapon.doSheath()


		char = self.objects.get("Character", None)
		if char == None:
			return

		char["WP_ACTIVE"] = str(weap["ACTIVE"])
		char["WP_TIMER"] = str(weap["TIMER"])
		if self.active_weapon != None:
			char["WP_CLASS"] = self.active_weapon.NAME+str(dict["ID"])
		else:
			char["WP_CLASS"] = "None"+str(dict["ID"])

	class WeaponFallback:
		NAME = "Fallback_WP"

		def __init__(self, plr):
			self.owning_player = plr

			self.data = {}
			self.data["HUD"] = {"Stat":"", "Text":""}

		def doDraw(self):
			return True

		def doSheath(self):
			self.owning_player.active_weapon = None
			return True

		def RUN(self):
			pass





