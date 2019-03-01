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


import os.path as ospath

import math
import mathutils

from bge import logic

from . import settings, keymap, config


SC_SCN = logic.getCurrentScene()
SC_HUD = None
SC_CAM = SC_SCN.active_camera
SC_RUN = None

CURRENT = logic.globalDict["CURRENT"]

CUR_LVL = str(CURRENT["Level"])+SC_SCN.name
CUR_PRF = CURRENT["Profile"]
CUR_PLR = CURRENT["Player"]

PROFILE = logic.globalDict["PROFILES"][CUR_PRF]

LEVEL = None

DATA = logic.globalDict["DATA"]

del CUR_LVL, CUR_PRF, CUR_PLR

ACTIVE_LIBLOAD = None


def MAIN(cont):
	for cls in logic.UPDATELIST:
		try:
			cls.RUN()
		except Exception as ex:
			logic.UPDATELIST.remove(cls)
			print("FATAL RUNTIME ERROR:", cls.__class__)
			print("\t", ex)

	if logic.VIEWPORT != None:
		try:
			logic.VIEWPORT.RUN()
		except Exception as ex:
			logic.VIEWPORT = None
			print("FATAL RUNTIME ERROR:", "CoreViewport")
			print("\t", ex)

	if keymap.SYSTEM["SCREENSHOT"].tap() == True:
		logic.globalDict["SCREENSHOT"]["Trigger"] = True


def LIBCB(status):
	global ACTIVE_LIBLOAD
	print("ASYNC:", status.libraryName)
	ACTIVE_LIBLOAD = None

def GAME(cont):
	global CURRENT, LEVEL, DATA, PROFILE, ACTIVE_LIBLOAD

	global SC_SCN, SC_RUN
	SC_SCN = cont.owner.scene
	SC_RUN = cont.owner

	scene = SC_SCN
	owner = SC_RUN

	spawn = owner.get("SPAWN", True)
	timer = owner.get("TIMER", None)
	black = owner.get("GFXBG", None)

	if spawn == False:
		MAIN(cont)
		return "DONE"

	## SET SCENE ##
	if CURRENT["Scene"] != None and config.EMBEDDED_FIX == False:
		if CURRENT["Scene"] != scene.name:
			if scene.replace(CURRENT["Scene"]) == True:
				CURRENT["Level"] = None
				print(scene.name, CURRENT["Scene"])
				return "SCENE"
			else:
				print("NOTICE: Scene '"+CURRENT["Scene"]+"' Not Found...")

	CURRENT["Scene"] = scene.name

	## LEVEL DATA ##
	if CURRENT["Level"] == None and owner.get("MAP", None) != None:
		CURRENT["Level"] = owner["MAP"]+".blend"

	newmap = str(CURRENT["Level"])+scene.name

	if newmap not in PROFILE["LVLData"]:
		print("Initializing Level Data...", newmap)
		PROFILE["LVLData"][newmap] = settings.GenerateLevelData()

	LEVEL = PROFILE["LVLData"][newmap]

	if config.EMBEDDED_FIX == True:
		owner["SPAWN"] = False
		return "DONE"

	if black == None:
		owner["GFXBG"] = True
		return "BLACK"

	## LIBLOAD ##
	if owner.get("LIBLIST", None) == None:
		coreblend = ospath.normpath(__file__+"\\..\\CoreAssets.blend")
		owner["LIBLIST"] = [coreblend]
		for libblend in config.LIBRARIES:
			libblend = DATA["GAMEPATH"]+"CONTENT\\"+libblend+".blend"
			owner["LIBLIST"].append(libblend)
		return "LIBLOAD"

	if ACTIVE_LIBLOAD != None:
		print(ACTIVE_LIBLOAD.libraryName, ACTIVE_LIBLOAD.progress)
		return "LIBLOAD"

	if len(owner["LIBLIST"]) > 0:
		libblend = owner["LIBLIST"].pop(0)
		if config.LIBLOAD_TYPE != "ASYNC" or config.ASYNC_FIX == True:
			logic.LibLoad(libblend, "Scene", load_actions=True, verbose=False, load_scripts=True)
			print(libblend)
		elif config.LIBLOAD_TYPE == "ASYNC":
			ACTIVE_LIBLOAD = logic.LibLoad(libblend, "Scene", load_actions=True, verbose=False, load_scripts=True, async=True)
			ACTIVE_LIBLOAD.onFinish = LIBCB

		return "LIBLOAD"

	## HUD SCENE ##
	if timer == None:
		owner["TIMER"] = (config.UPBGE_FIX == False)*25

		owner.worldScale = [1,1,1]
		logic.addScene("HUD", 1)
		return "HUD"

	elif timer <= 30:
		owner["TIMER"] += 1
		return "TIMER"

	## SPAWN ##
	if "CLIP" in owner:
		LEVEL["CLIP"] = owner["CLIP"]

	if CURRENT["Player"] == None:
		CURRENT["Player"] = owner.get("PLAYER", config.DEFAULT_PLAYER)

	if CURRENT["Player"] not in scene.objectsInactive:
		CURRENT["Player"] = config.DEFAULT_PLAYER

	if spawn == True:
		LOAD(owner)
		owner["SPAWN"] = None
		return "SPAWN"

	elif spawn == None:
		owner["SPAWN"] = False
		return "END"

	return "WAIT"


def LOAD(owner):
	global CURRENT, LEVEL, DATA, PROFILE

	scene = owner.scene

	from . import viewport
	logic.VIEWPORT = viewport.CoreViewport()

	## Ground Detector ##
	for obj in scene.objects:
		gnd = obj.get("GROUND", None)
		cam = obj.get("CAMERA", None)
		if gnd == False:
			del obj["GROUND"]
		elif obj.getPhysicsId() != 0:
			obj["GROUND"] = True
		if cam == False:
			del obj["CAMERA"]
		else:
			obj["CAMERA"] = True

	## Add Player ##
	char = scene.addObject(CURRENT["Player"], owner, 0)
	print("PLAYER:", CURRENT["Player"], char.worldPosition)

	## Spawn New Objects ##
	cleanup = []

	for obj in scene.objects:
		split = obj.name.split(".")
		name = None

		if obj != owner and split[0] == "Spawn" and len(split) > 1:
			name = obj.get("OBJECT", split[1])

		if name != None:
			cleanup.append(obj)
			obj.worldScale = [1,1,1]

			if obj.get("SPAWN", True) == True and obj.name not in LEVEL["SPAWN"]:
				if name in scene.objectsInactive:
					newobj = scene.addObject(name, obj, 0)
					for prop in obj.getPropertyNames():
						if prop not in ["SPAWN", "OBJECT", "DICT", "GROUND", "CAMERA"]:
							newobj[prop] = obj[prop]
					newobj["DICT"] = {"Object":name, "Data":None, "Add":obj.name}
					print("SPAWNED:", name, newobj.worldPosition)
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
		#if "SCL" in drop["Data"]:
		#	newobj.worldScale = drop["Data"]["SCL"]
		newobj["DICT"] = drop
		print("CYBERSPACE:", drop["Object"])

	LEVEL["DROP"] = []


class CoreObject:

	NAME = "Object"
	UPDATE = True
	GHOST = False
	LOCK = ""
	WORLDDOOR = False
	ANIMOBJ = None
	HUDLAYOUT = None

	def __init__(self):
		owner = logic.getCurrentController().owner

		owner["Class"] = self

		owner["RAYCAST"] = owner.get("RAYCAST", None)
		owner["RAYNAME"] = self.NAME

		self.objects = {"Root":owner}

		self.dict = owner["DICT"]
		self.data = self.defaultData()

		self.defaultStates()

		self.checkGhost(owner)
		self.applyGravity()
		self.findObjects(owner)
		self.doLoad()

		self.ST_Startup()

	def defaultStates(self):
		self.active_pre = []
		self.active_state = self.ST_Disabled
		self.active_post = []

	def defaultData(self):
		return {}

	def findObjects(self, obj, ground=None):
		dict = self.objects
		group = []
		list = []

		for child in obj.childrenRecursive:
			if ground == True:
				child["GROUND"] = True
			elif ground == None:
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

	def createMatrix(self, rot=None, deg=True, mirror="", mat=None):
		if mat != None:
			return mathutils.Matrix(mat)
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

		if self.COLCB not in obj.collisionCallbacks:
			self.clearCollisionList()
			obj.collisionCallbacks.append(self.COLCB)

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
		elif "GROUND" in obj:
			del obj["GROUND"]

	def applyGravity(self, grav=None):
		owner = self.objects.get("Root", None)
		if grav == None:
			grav = SC_SCN.gravity

		self.gravity = self.createVector(vec=grav)

	def saveWorldPos(self):
		obj = self.objects["Root"]
		self.data["POS"] = self.vecTuple(obj.worldPosition)
		self.data["ORI"] = self.matTuple(obj.worldOrientation)
		self.data["SCL"] = self.vecTuple(obj.worldScale)

	def doLoad(self):
		owner = self.objects["Root"]

		if self not in logic.UPDATELIST:
			logic.UPDATELIST.append(self)

		if self.dict["Data"] == None:
			self.dict["Data"] = self.data
			self.data["ACTIVE_STATE"] = self.active_state.__name__
			self.saveWorldPos()
		else:
			self.data = self.dict["Data"]
			self.active_state = getattr(self, self.data["ACTIVE_STATE"])

		if self.UPDATE == False:
			return

		global LEVEL
		if "Add" in self.dict:
			LEVEL["SPAWN"].append(self.dict["Add"])
			del self.dict["Add"]

	def doUpdate(self):
		owner = self.objects["Root"]

		self.saveWorldPos()

		global LEVEL
		if self.dict not in LEVEL["DROP"]:
			LEVEL["DROP"].append(self.dict)

	def getLocalSpace(self, obj, pnt):
		if type(pnt) != mathutils.Vector:
			pnt = mathutils.Vector(pnt)
		lp = pnt - obj.worldPosition
		lp = obj.worldOrientation.inverted()*lp
		return lp

	def getWorldSpace(self, obj, pnt):
		if type(pnt) != mathutils.Vector:
			pnt = mathutils.Vector(pnt)
		wp = obj.worldOrientation*pnt
		wp = wp + obj.worldPosition
		return wp

	def getTransformDiff(self, obj):
		root = self.objects["Root"]

		pnt = root.worldPosition-obj.worldPosition
		lp = list(obj.worldOrientation.inverted()*pnt)

		dr = obj.worldOrientation
		pr = root.worldOrientation
		lr = self.matTuple(dr.inverted()*pr)

		return lp, lr

	def teleportTo(self, pos=None, ori=None, vel=False):
		owner = self.objects["Root"]

		if pos != None:
			owner.worldPosition = pos
		if ori != None:
			owner.worldOrientation = ori
		if vel == False:
			owner.worldLinearVelocity = (0,0,0)

	def hideObject(self, state=True):
		state = (state==False)
		self.objects["Root"].setVisible(state, True)

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

		if CHECK == "FRAME":
			ACTCHK = OBJECT.getActionFrame(LAYER)
			return ACTCHK
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

	def alignToGravity(self, obj=None, axis=2, neg=False):
		if obj == None:
			obj = self.objects["Root"]
		if self.gravity.length >= 0.1:
			grav = self.gravity.normalized()
			if neg == False:
				grav = -grav
			obj.alignAxisToVect(grav, axis, 1.0)

	def checkStability(self, align=False, offset=1.0, override=False):
		if settings.config.DO_STABILITY == False or self.gravity.length < 0.1:
			return

		obj = self.objects["Root"]

		grav = self.gravity.normalized()
		rayto = obj.worldPosition+grav

		down, pnt, nrm = obj.rayCast(rayto, None, 20000, "GROUND", 1, 1, 0)

		if nrm != None:
			if nrm.dot(grav) > 0:
				down = None
		if down == None or override == True:
			up, pnt, nrm = obj.rayCast(rayto, None, -10000, "GROUND", 1, 1, 0)
			if up != None:
				if override == True:
					obj.worldLinearVelocity = (0,0,0)
				obj.worldPosition = pnt+(nrm*offset)
				if align == True:
					obj.alignAxisToVect(nrm, 2, 1.0)
			#elif obj.getPhysicsId() != 0:
			#	obj.applyForce(-self.gravity*obj.mass, False)

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
		gc = []
		for run in self.active_pre:
			st = run()
			if st == "REMOVE":
				gc.append(run)
		for i in gc:
			self.active_pre.remove(i)

	def runStates(self):
		if self.active_state != None:
			self.active_state()
			self.data["ACTIVE_STATE"] = self.active_state.__name__

	def runPost(self):
		gc = []
		for run in self.active_post:
			st = run()
			if st == "REMOVE":
				gc.append(run)
		for i in gc:
			self.active_post.remove(i)

	def RUN(self):
		self.runPre()
		self.runStates()
		self.runPost()
		self.clearRayProps()


class CoreAdvanced(CoreObject):

	WP_TYPE = "RANGED"
	WP_SOCKETS = []
	INVENTORY = {}
	SLOTS = {}

	CAM_TYPE = "THIRD"
	CAM_ORBIT = False
	CAM_RANGE = (4,16)
	CAM_HEIGHT = 0.1
	CAM_STEPS = 5
	CAM_ZOOM = 2
	CAM_MIN = 0.5
	CAM_SLOW = 10
	CAM_FOV = 90

	CAM_SHDIST = 0.3
	CAM_SHSIDE = 0.3

	HUDLAYOUT = None

	def defaultData(self):
		return {"HEALTH":100, "ENERGY":100}

	def PR_Modifiers(self):
		for dict in self.data["POWERUPS"]:
			dict["__TIMER__"] = dict.get("__TIMER__", 0) - 1

			self.data["HEALTH"] += dict.get("HEALTH", 0)
			self.data["ENERGY"] += dict.get("ENERGY", 0)

			if "KEYRING" in dict:
				self.data["KEYRING"].append(dict["KEYRING"])

	def PS_Attachments(self):
		for slot in self.cls_dict:
			self.cls_dict[slot].RUN()

		for dict in self.data["POWERUPS"]:
			if dict["__TIMER__"] < 0:
				self.data["POWERUPS"].remove(dict)

	def loadInventory(self, owner):
		scene = owner.scene

		self.cls_dict = {}
		self.active_weapon = None

		self.active_pre.insert(0, self.PR_Modifiers)
		self.active_post.append(self.PS_Attachments)

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

		#char = self.objects.get("Character", None)
		#if char == None:
		#	return

		#char["WP_ACTIVE"] = ""
		#char["WP_TIMER"] = ""
		#char["WP_CLASS"] = ""
		#char.addDebugProperty("WP_ACTIVE", True)
		#char.addDebugProperty("WP_TIMER", True)
		#char.addDebugProperty("WP_CLASS", True)

	def buildInventory(self):
		if "INVENTORY" in self.data:
			return self.data["INVENTORY"]

		self.data["WPDATA"] = {"ACTIVE":"NONE", "CURRENT":"NONE", "TIMER":0, "WHEEL":{}}

		for mode in ["MELEE", "RANGED"]:
			self.data["WPDATA"]["WHEEL"][mode] = {"ID":-1, "LIST":[]}

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
		self.data["KEYRING"] = [""]
		self.data["POWERUPS"] = []

		defaults = self.INVENTORY
		items = []

		for slot in defaults:
			dict = {"Object":defaults[slot], "Data":None, "Equiped":slot}
			items.append(dict)

		return items

	def weaponManager(self):
		weap = self.data["WPDATA"]

		## MODE SWITCH ##
		modes = []
		for mode in weap["WHEEL"]:
			if len(weap["WHEEL"][mode]["LIST"]) >= 1:
				modes.append(mode)
			else:
				weap["WHEEL"][mode]["ID"] = -1

		if len(modes) >= 1:
			if weap["CURRENT"] == "NONE":
				if self.WP_TYPE in modes:
					weap["CURRENT"] = self.WP_TYPE
				else:
					weap["CURRENT"] = modes[0]

			elif keymap.BINDS["WP_MODE"].tap() == True and len(modes) == 2:
				if weap["CURRENT"] == "MELEE":
					weap["CURRENT"] = "RANGED"
				elif weap["CURRENT"] == "RANGED":
					weap["CURRENT"] = "MELEE"

		else:
			weap["CURRENT"] = "NONE"
			return

		dict = weap["WHEEL"][weap["CURRENT"]]

		## WEAPON SELECT ##
		if dict["ID"] >= len(dict["LIST"]):
			dict["ID"] = len(dict["LIST"])-1

		if dict["ID"] == -1:
			if len(dict["LIST"]) >= 1:
				dict["ID"] = 0
			else:
				return

		elif keymap.BINDS["WP_UP"].tap() == True and weap["ACTIVE"] != "SWITCH":
			dict["ID"] += 1
			weap["TIMER"] = 0
			if dict["ID"] == len(dict["LIST"]):
				dict["ID"] = 0

		elif keymap.BINDS["WP_DOWN"].tap() == True and weap["ACTIVE"] != "SWITCH":
			dict["ID"] -= 1
			weap["TIMER"] = 0
			if dict["ID"] == -1:
				dict["ID"] = len(dict["LIST"])-1

		## STATE MANAGER ##
		if weap["ACTIVE"] == "ACTIVE":
			if self.active_weapon != None:

				slot = dict["LIST"][dict["ID"]]

				if self.active_weapon != self.cls_dict[slot]:
					if weap["TIMER"] == 10:
						check = self.active_weapon.stateSwitch(False)
						if check == True:
							weap["TIMER"] = 0
							weap["ACTIVE"] = "SWITCH"

					else:
						weap["TIMER"] += 1

				## STATE PASSIVE ##
				if keymap.BINDS["SHEATH"].tap() == True:
					check = self.active_weapon.stateSwitch(False)
					if check == True:
						weap["TIMER"] = 0
						weap["ACTIVE"] = "NONE"

			else:
				weap["TIMER"] = 0
				weap["ACTIVE"] = "NONE"

		elif weap["ACTIVE"] == "SWITCH":
			if self.active_weapon == None:

				slot = dict["LIST"][dict["ID"]]
				self.active_weapon = self.cls_dict[slot]

				check = self.active_weapon.stateSwitch(True)

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
				self.active_weapon.stateSwitch(False)


		#char = self.objects.get("Character", None)
		#if char == None:
		#	return

		#char["WP_ACTIVE"] = str(weap["ACTIVE"])
		#char["WP_TIMER"] = str(weap["TIMER"])
		#if self.active_weapon != None:
		#	char["WP_CLASS"] = self.active_weapon.NAME+str(dict["ID"])
		#else:
		#	char["WP_CLASS"] = "None"+str(dict["ID"])






