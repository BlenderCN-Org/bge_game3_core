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

## PLAYER CLASS ##


from bge import logic

import PYTHON.keymap as keymap
import PYTHON.base as base
import PYTHON.HUD as HUD

if "CURRENT" in logic.globalDict:
	logic.LibLoad( base.DATA["GAMEPATH"] + "CONTENT\\Game Assets.blend", "Scene", load_actions=True, verbose=False, load_scripts=True, async=False)
	logic.LibLoad( base.DATA["GAMEPATH"] + "CONTENT\\Player.blend",      "Scene", load_actions=True, verbose=False, load_scripts=True, async=False)
	logic.LibLoad( base.DATA["GAMEPATH"] + "CONTENT\\Stargate.blend",    "Scene", load_actions=True, verbose=False, load_scripts=True, async=False)
	logic.LibLoad( base.DATA["GAMEPATH"] + "CONTENT\\Cinematics.blend",  "Scene", load_actions=True, verbose=False, load_scripts=True, async=False)

	BLACK = base.SC_SCN.addObject("GFX_Black", base.SC_CAM, 0)
	BLACK.setParent(base.SC_CAM)
	BLACK.color = (0, 0, 0, 1)

logic.PLAYERCLASS = None


def SPAWN(cont):
	owner = cont.owner
	scene = owner.scene
	spawn = owner.get("SPAWN", True)

	if "CURRENT" not in logic.globalDict:
		return

	if "CLIP" in owner:
		base.LEVEL["CLIP"] = owner["CLIP"]

	if "POS" not in base.LEVEL["PLAYER"]:
		WP = owner.worldPosition
		WO = owner.worldOrientation
		base.LEVEL["PLAYER"]["POS"] = list(WP)
		base.LEVEL["PLAYER"]["ORI"] = [list(WO[0]), list(WO[1]), list(WO[2])]

	if base.CURRENT["Player"] == None:
		player = owner.get("PLAYER", "Actor")
		base.CURRENT["Player"] = player
	else:
		player = base.CURRENT["Player"]


	if spawn == False:
		owner.endObject()
		return

	elif spawn == True:
		scene.addObject(player, owner, 0)
		owner["SPAWN"] = None
		return

	elif spawn == None:
		global BLACK
		BLACK.endObject()
		BLACK = None
		owner["SPAWN"] = False


class CorePlayer(base.CoreAdvanced):

	NAME = "Player"
	MESH = "Actor"
	PORTAL = True
	CLASS = "Standard"
	HAND = {"MAIN":"Hand_R", "OFF":"Hand_L"}
	WP_TYPE = "RANGED"
	SLOTS = {"ONE":"Hip_L", "TWO":"Hip_R", "FOUR":"Shoulder_L", "FIVE":"Back", "SIX":"Shoulder_R"}
	ACCEL = 10
	Z_OFF = 0.2
	EYE_H = 1.6
	FOV = 90
	SLOPE = 60
	STATS = {}

	def __init__(self):
		scene = base.SC_SCN
		char = logic.getCurrentController().owner

		self.objects = {"Root":None, "Character":char}

		self.findObjects(char)

		self.ANIMOBJ = self.objects["Rig"]
		self.doAnim(NAME="Jumping", FRAME=(0,0))

		self.active_pre = []
		self.active_state = self.ST_Walking
		self.active_post = [self.PS_Recharge, self.PS_GroundTrack]

		self.jump_state = "NONE"
		self.jump_timer = 0
		self.crouch = 0
		self.rayorder = "NONE"

		self.rayhit = None
		self.rayvec = None

		self.groundhit = None
		self.groundobj = None
		self.groundpos = [self.createVector(), self.createVector()]
		self.groundori = [self.createMatrix(), self.createMatrix()]

		self.motion = {"Move":self.createVector(2), "Rotate":self.createVector(3), "Climb":0, "Accel":0}

		self.data = {"HEALTH":100, "ENERGY":100, "SPEED":0.1, "JUMP":6, "RUN":True, "RECHARGE":0.1}
		self.data["CAMERA"] = {"State":3, "Orbit":True, "Zoom":4, "Dist":4, "Range":(1,6), "FOV":[self.FOV, 90], "ZR":[0,1,0], "XR":0}
		self.data["HUD"] = {"Text":"", "Color":(0,0,0,0.5), "Target":None, "Locked":None}

		self.data["DAMPING"] = [1.0, 1.0]
		self.data["LINVEL"] = [0,0,0]
		self.data["JP_STATE"] = self.jump_state
		self.data["JP_TIMER"] = self.jump_timer
		self.data["GB_STATE"] = self.rayorder

		dict = self.defaultData()
		for key in dict:
			if key not in self.data:
				self.data[key] = dict[key]

		for stat in self.STATS:
			self.data[stat] = self.STATS[stat]

		char["Class"] = self
		char["DEBUG1"] = ""
		char["DEBUG2"] = ""
		char["RAYTEXT"] = ""
		char.addDebugProperty("DEBUG1", True)
		char.addDebugProperty("DEBUG2", True)
		char.addDebugProperty("RAYTEXT", True)

		self.doLoad()
		self.loadInventory(char)

		if logic.PLAYERCLASS == None:
			logic.PLAYERCLASS = self

			portal = base.LOAD(char)

			if portal != None:
				portal["RAYCAST"] = self

			owner = scene.addObject("Player", char, 0)
			owner.setDamping(self.data["DAMPING"][0], self.data["DAMPING"][1])
			owner["Class"] = self

			self.objects["Root"] = owner

			self.addCollisionCallBack()
			self.findObjects(owner)
			self.parentArmature(owner)

			self.doPortal()

			logic.HUDCLASS = HUD.SceneManager(self)

			keymap.MOUSELOOK.center()
			self.doCameraCollision()
			self.setCamera()

		self.ST_Startup()

	def doPortal(self):
		scene = base.SC_SCN
		owner = self.objects["Root"]

		door = base.DATA["Portal"]["Door"]
		zone = base.DATA["Portal"]["Zone"]
		portal = scene.objects.get(str(door), None)

		if portal == None:
			owner.worldPosition = base.LEVEL["PLAYER"]["POS"]
			owner.worldOrientation = base.LEVEL["PLAYER"]["ORI"]

		elif zone != None:
			pos = self.createVector(vec=zone[0])
			pos = portal.worldPosition+(portal.worldOrientation*pos)

			dr = portal.worldOrientation.to_euler()
			ori = (zone[1][0]+dr[0], zone[1][1]+dr[1], zone[1][2]+dr[2])
			ori = self.createMatrix(rot=ori, deg=False)

			owner.worldPosition = pos
			owner.worldOrientation = ori

		else:
			owner.worldPosition = portal.worldPosition.copy()
			owner.worldOrientation = portal.worldOrientation.copy()

		self.alignCamera(axis=self.data["CAMERA"]["ZR"])
		self.objects["CamRot"].applyRotation([self.data["CAMERA"]["XR"],0,0], True)

		owner.localLinearVelocity = self.data["LINVEL"]

		if base.DATA["Portal"]["Vehicle"] == None or portal == None:
			base.DATA["Portal"]["Door"] = None
			base.DATA["Portal"]["Zone"] = None

	def doLoad(self):
		if self.NAME in base.PROFILE["PLRData"]:
			self.data = base.PROFILE["PLRData"][self.NAME]
		else:
			base.PROFILE["PLRData"][self.NAME] = self.data

		#self.active_state = getattr(self, self.data["ACTIVE_STATE"])

		self.jump_state = self.data["JP_STATE"]
		self.jump_timer = self.data["JP_TIMER"]
		self.rayorder = self.data["GB_STATE"]

	def doUpdate(self, world=True, vehicle=False):
		owner = self.objects["Root"]

		self.data["JP_STATE"] = self.jump_state
		self.data["JP_TIMER"] = self.jump_timer
		self.data["GB_STATE"] = self.rayorder

		self.data["LINVEL"] = self.vecTuple(owner.localLinearVelocity)

		self.data["DAMPING"] = [owner.linearDamping, owner.angularDamping]

		self.data["CAMERA"]["ZR"] = list(owner.worldOrientation.inverted()*self.objects["VertRef"].getAxisVect([0,1,0]))
		self.data["CAMERA"]["XR"] = list(self.objects["CamRot"].localOrientation.to_euler())[0]

		base.LEVEL["PLAYER"]["POS"] = self.vecTuple(owner.worldPosition)
		base.LEVEL["PLAYER"]["ORI"] = self.matTuple(owner.worldOrientation)

		if world == True:
			for cls in logic.UPDATELIST:
				cls.doUpdate()

	def parentArmature(self, obj, offset=False):
		char = self.objects["Character"]

		if offset == True:
			Z = self.Z_OFF
		else:
			Z = 0

		char.setParent(obj)
		char.localPosition = (0, 0, Z)
		char.localOrientation = self.createMatrix()

	def enterVehicle(self, seat, action="Jumping"):
		self.jump_state = "NONE"
		self.jump_timer = 0
		self.crouch = 0
		self.doCrouch(False)
		self.rayorder = "NONE"
		self.data["HUD"]["Target"] = None
		self.data["HUD"]["Text"] = ""

		self.doUpdate(False)

		if self.objects["Root"] != None:
			self.objects["Character"].removeParent()
			self.objects["Root"].endObject()
			self.objects["Root"] = None

		self.parentArmature(seat, True)

		self.doAnim(NAME=action, FRAME=(0,0), MODE="LOOP")

	def exitVehicle(self, spawn):
		scene = base.SC_SCN

		keymap.MOUSELOOK.center()

		self.doAnim(NAME="Jumping", FRAME=(0,0))

		self.objects["Character"].removeParent()

		owner = scene.addObject("Player", spawn, 0)
		self.objects["Root"] = owner

		self.addCollisionCallBack()

		self.findObjects(owner)
		self.parentArmature(owner)
		self.alignCamera()
		self.setCamera()

		logic.HUDCLASS.setControl(self)

		owner["Class"] = self

	def switchPlayerPassive(self, owner):
		self.jump_state = "NONE"
		self.jump_timer = 0
		self.crouch = 0
		self.doCrouch(False)
		self.rayorder = "NONE"
		self.data["HUD"]["Target"] = None
		self.data["HUD"]["Text"] = ""

		self.doUpdate(False)

		self.objects["Character"].removeParent()
		self.objects["Root"] = None

		self.parentArmature(owner)

		self.doAnim(NAME="Jumping", FRAME=(0,0))

	def switchPlayerActive(self, owner):
		self.objects["Root"] = owner

		keymap.MOUSELOOK.center()

		self.doAnim(STOP=True)

		self.findObjects(owner)
		self.parentArmature(owner)
		self.setCamera()

		self.addCollisionCallBack()

		logic.HUDCLASS.setControl(self)

		owner["Class"] = self
		logic.PLAYERCLASS = self
		base.CURRENT["Player"] = self.objects["Character"].name

	def alignCamera(self, factor=1.0, axis=(0,1,0), up=(0,0,1)):
		vref = self.objects["Root"].getAxisVect(axis)
		self.objects["VertRef"].alignAxisToVect(vref, 1, factor)
		self.objects["VertRef"].alignAxisToVect(up, 2, 1.0)

	def alignPlayer(self, factor=1.0, axis=None, up=(0,0,1)):
		if axis == None:
			axis = self.objects["VertRef"].getAxisVect((0,1,0))
		self.objects["Root"].alignAxisToVect(axis, 1, factor)
		self.objects["Root"].alignAxisToVect(up, 2, 1.0)

	def setCameraEye(self, axis=2, neg=False):

		if self.EYE_H > 1.75:
			eye = 1.75
		else:
			eye = self.EYE_H

		for id in [0, 1, 2]:
			x = 0
			if id == axis:
				x = eye-1
			if neg == True:
				x = -1*x

			self.objects["CamRot"].localPosition[id] = x

		self.objects["WallRay"].localPosition[2] = eye+0.2

	def setCameraFOV(self, fov=None):
		if fov == None:
			fov = self.data["CAMERA"]["FOV"][0]
			self.data["CAMERA"]["FOV"][1] = fov
		cam = self.objects["CamThird"]
		cam.fov = fov

	def setCamera(self, CAM=0):
		base.SC_SCN.active_camera = self.objects["CamThird"]
		self.setCameraEye()
		self.setCameraFOV()

	#def getCameraDirection(self):
	#	owner = self.objects["Root"]
	#	camd = self.objects["VertRef"]
	#	return owner.worldOrientation.inverted()*camd.getAxisVect([0,1,0])

	def getDropPoint(self):
		drop = self.objects["Ray"].worldPosition.copy()

		if self.rayhit != None:
			if self.rayvec.length <= 1:
				drop = self.rayhit[1]#+self.rayhit[2]

		return list(drop)

	def getInputs(self):

		TURN = keymap.BINDS["PLR_TURNLEFT"].axis() - keymap.BINDS["PLR_TURNRIGHT"].axis()
		LOOK = keymap.BINDS["PLR_LOOKUP"].axis() - keymap.BINDS["PLR_LOOKDOWN"].axis()

		MOVE = keymap.BINDS["PLR_FORWARD"].axis() - keymap.BINDS["PLR_BACKWARD"].axis()
		STRAFE = keymap.BINDS["PLR_STRAFERIGHT"].axis() - keymap.BINDS["PLR_STRAFELEFT"].axis()
		CLIMB = 0

		## Key Commands ##
		if keymap.BINDS["PLR_FORWARD"].active() == True:
			MOVE = 1

		if keymap.BINDS["PLR_BACKWARD"].active() == True:
			MOVE = -1

		if keymap.BINDS["PLR_STRAFERIGHT"].active() == True:
			STRAFE = 1

		if keymap.BINDS["PLR_STRAFELEFT"].active() == True:
			STRAFE = -1

		if keymap.BINDS["PLR_JUMP"].active() == True:
			CLIMB = 1

		if keymap.BINDS["PLR_DUCK"].active() == True:
			CLIMB = -1

		if keymap.BINDS["PLR_TURNLEFT"].active() == True:
			TURN += 1

		if keymap.BINDS["PLR_TURNRIGHT"].active() == True:
			TURN -= 1

		if keymap.BINDS["PLR_LOOKUP"].active() == True:
			LOOK += 1

		if keymap.BINDS["PLR_LOOKDOWN"].active() == True:
			LOOK -= 1

		if keymap.BINDS["PLR_RUN"].tap() == True:
			self.data["RUN"] ^= True

		self.motion["Move"][0] = STRAFE
		self.motion["Move"][1] = MOVE
		self.motion["Climb"] = CLIMB

		self.motion["Rotate"][0] = LOOK
		self.motion["Rotate"][1] = 0
		self.motion["Rotate"][2] = TURN

		for slot in self.data["SLOTS"]:
			key = self.data["SLOTS"][slot]
			if slot in self.data["INVSLOT"] and keymap.BINDS[key].tap() == True:
				dict = self.data["INVSLOT"][slot]
				if keymap.SYSTEM["ALT"].checkModifiers() == True:
					dict["Data"]["POS"] = self.getDropPoint()
					dict["Equiped"] = "DROP"
				else:
					dict["Data"]["ENABLE"] ^= True

		if keymap.BINDS["SUPER_DROP"].tap() == True:
			WPDROP = self.getDropPoint()
			for dict in self.data["INVENTORY"]:
				dict["Data"]["POS"] = WPDROP.copy()
				dict["Equiped"] = "DROP"
				WPDROP[2] += 2
			for dict in self.data["WEAPONS"]:
				dict["Data"]["POS"] = WPDROP.copy()
				dict["Equiped"] = "DROP"
				WPDROP[2] += 2

		if keymap.SYSTEM["SCREENSHOT"].tap() == True:
			self.doScreenshot()

	def doCameraState(self):
		camdata = self.data["CAMERA"]

		if camdata["State"] == 1:
			camdata["Dist"] += (0-camdata["Dist"])*0.1

			if self.rayhit != None:
				v = self.objects["CamThird"].getVectTo(self.rayhit[1])
				self.objects["CamThird"].alignAxisToVect(-v[1], 2, 0.05)
				xref = self.objects["CamRot"].getAxisVect([1,0,0])
				self.objects["CamThird"].alignAxisToVect(xref, 0, 0.05)

			## Toggle ##
			if keymap.BINDS["TOGGLECAM"].tap() == True:
				camdata["State"] = 2
				camdata["FOV"][0] = self.FOV

			if self.motion["Move"].length > 0.01 or self.jump_state != "NONE":
				camdata["State"] = 2
				camdata["FOV"][0] = self.FOV

		else:
			camdata["Dist"] += (camdata["Zoom"]-camdata["Dist"])*0.1

			## Set Camera Zoom ##
			if keymap.BINDS["ZOOM_IN"].tap() == True and camdata["Zoom"] > camdata["Range"][0]:
				camdata["Zoom"] -= 1

			elif keymap.BINDS["ZOOM_OUT"].tap() == True and camdata["Zoom"] < camdata["Range"][1]:
				camdata["Zoom"] += 1

			## Toggle ##
			if self.motion["Move"].length < 0.01 and self.jump_state == "NONE":
				if keymap.BINDS["TOGGLECAM"].tap() == True:
					camdata["State"] = 1
					camdata["FOV"][0] = 60
				if camdata["Zoom"] == 0:
					camdata["Zoom"] = 1
					camdata["State"] = 1
					camdata["FOV"][0] = 60

		if camdata["State"] == 2:
			zref = self.objects["CamRot"].getAxisVect([0,0,1])
			self.objects["CamThird"].alignAxisToVect(zref, 1, 0.1)
			xref = self.objects["CamRot"].getAxisVect([1,0,0])
			self.objects["CamThird"].alignAxisToVect(xref, 0, 0.1)

		if camdata["FOV"][0] != camdata["FOV"][1]:
			dif = round((camdata["FOV"][0]-camdata["FOV"][1]), 2)
			if abs(dif) < 0.01:
				camdata["FOV"][1] = camdata["FOV"][0]
			else:
				camdata["FOV"][1] += dif*0.1
		else:
			if camdata["State"] == 2:
				self.objects["CamThird"].localOrientation = self.createMatrix([90,0,0])
				camdata["State"] = 3

		self.setCameraFOV(camdata["FOV"][1])

		if camdata["Orbit"] == True:
			X, Y = keymap.MOUSELOOK.axis()
			ts = (camdata["FOV"][1]/self.FOV)**2

			rx = ((self.motion["Rotate"][2]*0.03) + X)*ts
			ry = ((self.motion["Rotate"][0]*0.03) + Y)*ts

			self.objects["VertRef"].applyRotation((0, 0, rx), True)
			self.objects["CamRot"].applyRotation((ry, 0, 0), True)

	def doCameraCollision(self):
		margin = 1
		height = 0.15
		dist = self.data["CAMERA"]["Dist"]

		camera = self.objects["CamThird"]
		rayfrom = self.objects["CamRot"]
		rayto = self.objects["CamRay"]

		rayto.localPosition = (0, -dist, dist*height)

		hyp = (dist+margin)**2 + ((dist+margin)*height)**2

		rayOBJ, rayPNT, rayNRM = self.objects["Root"].rayCast(rayto, rayfrom, hyp**0.5, "GROUND", 1, 1, 0)

		camLX = 0.0
		camLY = -dist
		camLZ = dist*height

		if rayOBJ:
			rayto.worldPosition = rayPNT

			margin = margin*(abs(rayto.localPosition[1])/(dist+margin))

			camLX = 0.0
			camLY = rayto.localPosition[1]+margin
			camLZ = rayto.localPosition[2]-(margin*height)

		if camLZ < 0.2:
			camLZ = 0.2

		camera.localPosition[0] = camLX
		camera.localPosition[1] = camLY
		camera.localPosition[2] = camLZ

	def checkGround(self):
		owner = self.objects["Root"]
		ground = None
		angle = 0
		slope = 1.0

		#if "X" not in self.objects:
		#	self.objects["X"] = owner.scene.addObject("PU_Health", owner, 0)

		#guide = self.objects["X"]

		rayOBJ, rayPNT, rayNRM = owner.rayCast(self.objects["GroundRay"], None, 1.3, "GROUND", 1, 1, 0)

		if rayOBJ != None:
			angle = owner.getAxisVect((0,0,1)).angle(rayNRM, 0)
			angle = round(self.toDeg(angle), 2)
			ground = [rayOBJ, rayPNT, None]
			#guide.worldPosition = rayPNT.copy()

			if angle > self.SLOPE:
				ground = None
			if self.jump_state != "NONE":
				if owner.worldPosition[2]-rayPNT[2] > (1+((angle/90)*0.3)):
					ground = None

			if ground != None:
				if angle > 5:
					rayNRM[2] = 0
					rayNRM = rayNRM.normalized()
					dot = owner.getAxisVect((0,1,0)).angle(rayNRM, 0)/1.571
					slope = 1-(abs(dot-1)*((angle/90)))

			self.groundpos.insert(0, rayOBJ.worldPosition.copy())
			self.groundpos.pop()
			self.groundori.insert(0, rayOBJ.worldOrientation.copy())
			self.groundori.pop()

			if self.groundobj != rayOBJ:
				self.groundobj = rayOBJ
				self.groundpos[1] = self.groundpos[0].copy()
				self.groundori[1] = self.groundori[0].copy()

			self.rayorder = "NONE"

		else:
			if self.rayorder == "NONE":
				self.rayorder = "START"

		self.groundhit = ground
		return ground, angle, slope

	def checkWall(self, z=True, axis=(0,1,0), simple=None, prop="GROUND"):
		owner = self.objects["Root"]
		#rayto = self.objects["WallRayTo"]

		#if "X" not in self.objects:
		#	self.objects["X"] = owner.scene.addObject("PU_Health", rayto, 0)
		#	self.objects["X"].setParent(rayto)

		#guide = self.objects["X"]
		ref = owner.getAxisVect(axis)
		dist = 0.7
		angle = -1

		if simple != None:
			dist = simple

		WALLOBJ, WALLPNT, WALLNRM = owner.rayCast(owner.worldPosition.copy()+ref, None, dist, prop, 1, 0, 0)

		if WALLOBJ != None:
			#guide.worldPosition = WALLPNT
			if simple != None:
				return WALLOBJ
			if z == False:
				WALLNRM[2] = 0
				WALLNRM.normalize()
			if WALLNRM.length > 0.01:
				angle = ref.angle(WALLNRM, 0)
				angle = round(self.toDeg(angle), 2)

		else:
			if simple != None:
				return None

		self.checkEdge()

		return angle, WALLNRM

	def checkEdge(self):
		owner = self.objects["Root"]
		rayup = self.objects["WallRay"]
		rayto = self.objects["WallRayTo"]

		#if "XX" not in self.objects:
		#	self.objects["XX"] = owner.scene.addObject("PU_Health", rayto, 0)
		#	self.objects["XX"].setParent(rayto)
		#guide = self.objects["XX"]

		CHK = owner.rayCastTo(rayup, 0, "GROUND")

		EDGEOBJ, EDGEPNT, EDGENRM = owner.rayCast(rayto, rayup, 2.5, "GROUND", 1, 1, 0)

		if EDGEOBJ != None and CHK == None:
			#guide.worldPosition = EDGEPNT
			angle = self.createVector(vec=[0,0,1]).angle(EDGENRM, 0)
			angle = round(self.toDeg(angle), 2)
			dist = EDGEPNT[2]-owner.worldPosition[2]
			offset = self.EYE_H-0.67

			if dist > -1 and dist < 0.3: # and self.jump_state == "NONE":
				if self.motion["Move"].length > 0.01 and keymap.BINDS["PLR_JUMP"].tap() == True:
					if self.jump_state == "NONE" and dist < -0.5:
						pass
					elif owner.localLinearVelocity.length > -0.01:
						owner.worldPosition = [EDGEPNT[0], EDGEPNT[1], EDGEPNT[2]+1]
						self.jump_state = "FALLING"

			if owner.localLinearVelocity[2] < 0 and self.rayorder == "GRAB" and self.jump_state == "FALLING":
				if angle > self.SLOPE or "MOVE" in EDGEOBJ or abs(dist-offset) > 0.1:
					self.rayorder = "GRAB"
				else:
					WP = owner.worldPosition
					WP = [WP[0], WP[1], EDGEPNT[2]-offset]
					RP = [EDGEPNT[0], EDGEPNT[1], EDGEPNT[2]+1]
					self.rayorder = [WP, RP]
					self.jump_state = "EDGE"

		else:
			#guide.worldPosition = rayup.worldPosition.copy()
			if self.rayorder == "START":
				self.rayorder = "GRAB"
			elif self.jump_state == "EDGE":
				self.rayorder = "NONE"
				self.jump_state = "FALLING"

	def doInteract(self, range=2):
		scene = base.SC_SCN
		owner = self.objects["Root"]

		rayfrom = self.objects["CamRot"]
		rayto = self.objects["Ray"]
		dist = 200

		if self.data["CAMERA"]["State"] == 1:
			dist = 1000

		RAYHIT = owner.rayCast(rayto, rayfrom, dist, "", 1, 0, 0)

		RAYCOLOR = (0,0,0,0.5)
		RAYTARGPOS = [0.5, 0.5]

		self.rayhit = None
		self.rayvec = None

		if self.active_weapon != None:
			RAYCOLOR = (0,1,0,0.5)
			self.data["HUD"]["Text"] = self.active_weapon.NAME

		if RAYHIT[0] != None:
			self.rayhit = RAYHIT  #(RAYOBJ, RAYPNT, RAYNRM)
			self.rayvec = rayfrom.worldPosition.copy()-RAYHIT[1]

			RAYTARGPOS = scene.active_camera.getScreenPosition(RAYHIT[1])

			if self.rayvec.length < range:
				RAYOBJ = RAYHIT[0]

				if "RAYCAST" in RAYOBJ:
					if self.active_weapon != None:
						RAYCOLOR = (1,0,0,1)
					else:
						RAYCOLOR = (0,1,0,1)
						RAYOBJ["RAYCAST"] = self

				if RAYOBJ.get("RAYNAME", None) != None:
					self.data["HUD"]["Text"] = RAYOBJ["RAYNAME"]

		self.data["HUD"]["Color"] = RAYCOLOR
		self.data["HUD"]["Target"] = RAYTARGPOS

	def doJump(self):
		owner = self.objects["Root"]
		move = self.motion["Move"].normalized()

		if self.motion["Move"].length > 0.01:
			vref = self.objects["VertRef"].getAxisVect((move[0], move[1], 0))
			self.alignPlayer(axis=vref)

		owner.setDamping(0.3, 0.3)

		mx = self.data["SPEED"]
		if self.data["RUN"] == False or self.motion["Move"].length <= 0.5:
			mx = 0.03
		if self.ACCEL > 1:
			mx = mx*(self.motion["Accel"]/self.ACCEL)

		owner.localLinearVelocity[1] = self.data["JUMP"]*mx*6
		owner.localLinearVelocity[2] = self.data["JUMP"]

		self.doAnim(NAME="Jumping", FRAME=(0,20), PRIORITY=2, MODE="PLAY", BLEND=10)

	def doCrouch(self, state):
		if state == True or self.crouch != 0:
			self.objects["Root"].localScale[2] = 0.25
			self.objects["Character"].localScale[2] = 4
			self.active_state = self.ST_Crouch
		elif state == False:
			self.objects["Root"].localScale[2] = 1
			self.objects["Character"].localScale[2] = 1
			self.active_state = self.ST_Walking

	## INIT STATE ##
	def ST_Startup(self):
		if self.jump_state == "FLYING" and self.objects["Root"] != None:
			self.ST_Advanced_Set()

	## POST ##
	def PS_Recharge(self):
		self.data["ENERGY"] += self.data["RECHARGE"]
		if self.data["ENERGY"] > 100:
			self.data["ENERGY"] = 100

	def PS_GroundTrack(self):
		owner = self.objects["Root"]

		if self.groundhit == None or self.jump_state != "NONE":
			self.groundobj = None
			return

		rayOBJ = self.groundobj

		locOLD = owner.worldPosition - self.groundpos[1]
		posOLD = self.groundori[1].inverted()*locOLD

		locNEW = owner.worldPosition - self.groundpos[0]
		posNEW = self.groundori[0].inverted()*locNEW

		local = posOLD - posNEW
		offset = self.groundori[0]*local

		owner.worldPosition[0] += offset[0]
		owner.worldPosition[1] += offset[1]

		eulerOLD = self.groundori[1].to_euler()
		eulerNEW = self.groundori[0].to_euler()

		RZ = eulerOLD[2] - eulerNEW[2]

		owner.applyRotation((0, 0, -RZ), False)
		#self.objects["VertRef"].applyRotation((0, 0, -RZ), False)

	## WALKING STATE ##
	def ST_Crouch(self):
		scene = base.SC_SCN
		owner = self.objects["Root"]
		char = self.objects["Character"]

		ground, angle, slope = self.checkGround()

		if ground != None:
			owner.applyForce((0,0,-1*scene.gravity[2]), False)
			owner.worldPosition[2] = ground[1][2]+(1-(self.crouch*0.04))

			move = self.motion["Move"].normalized()

			if self.motion["Move"].length > 0.01:
				vref = self.objects["VertRef"].getAxisVect((move[0], move[1], 0))
				dref = self.objects["Root"].getAxisVect((0,1,0))
				dot = 1-((vref.dot(dref)*0.5)+0.5)
				dot = 0.2+((dot**2)*0.5)
				owner.alignAxisToVect(vref, 1, dot)

				mx = 0.015

				if self.ACCEL > 1:
					mx = mx*(self.motion["Accel"]/self.ACCEL)
					if self.motion["Accel"] < self.ACCEL:
						self.motion["Accel"] += 1

				mref = dref.copy()*mx
				owner.worldPosition[0] += mref[0]
				owner.worldPosition[1] += mref[1]

			else:
				self.motion["Accel"] = 0

		owner.alignAxisToVect((0,0,1), 2, 1.0)

		self.doInteract()
		self.checkStability()
		self.weaponManager()

		if keymap.BINDS["PLR_DUCK"].active() != True and self.checkWall(axis=(0,0,1), simple=1.4, prop="") == None:
			self.doAnim(NAME="Jumping", FRAME=(-5,-5), PRIORITY=3, MODE="LOOP", BLEND=10)
			if self.crouch <= 0:
				self.crouch = 0
				self.doCrouch(False)
			else:
				self.crouch -= 1

		else:
			if self.motion["Move"].length > 0.01:
				self.doAnim(NAME="Crouching", FRAME=(0,80), PRIORITY=3, MODE="LOOP", BLEND=10)
			else:
				self.doAnim(NAME="Crouching", FRAME=(0,0), PRIORITY=3, MODE="LOOP", BLEND=10)

			if self.crouch < 10:
				self.crouch += 1

	def ST_Walking(self):
		scene = base.SC_SCN
		owner = self.objects["Root"]
		char = self.objects["Character"]

		move = self.motion["Move"].normalized()

		ground, angle, slope = self.checkGround()

		wall, wallnrm = self.checkWall(z=False)

		if ground != None:
			if self.jump_state == "NONE":
				owner.applyForce((0,0,-1*scene.gravity[2]), False)
				owner.worldPosition[2] = ground[1][2]+(1+((angle/90)*0.3))

				still = keymap.SYSTEM["ALT"].checkModifiers()
				invck = 0
				for slot in self.cls_dict:
					if slot in ["Hip_L", "Hip_R"]:
						invck = -5

				if still == True:
					vref = self.objects["VertRef"].getAxisVect((0,1,0))
					dref = self.objects["Root"].getAxisVect((0,1,0))
					dot = 1-((vref.dot(dref)*0.5)+0.5)
					dot = 0.2+((dot**2)*0.3)
					owner.alignAxisToVect(vref, 1, dot)

				if keymap.BINDS["PLR_DUCK"].active() == True:
					self.doCrouch(True)

				elif keymap.BINDS["PLR_JUMP"].tap() == True:
					self.jump_state = "JUMP"
					self.jump_timer = 0
					self.doJump()

				elif self.motion["Move"].length > 0.01 and still == False:
					vref = self.objects["VertRef"].getAxisVect((move[0], move[1], 0))
					dref = self.objects["Root"].getAxisVect((0,1,0))
					dot = 1-((vref.dot(dref)*0.5)+0.5)
					dot = 0.2+((dot**2)*0.5)
					owner.alignAxisToVect(vref, 1, dot)

					if self.data["RUN"] == False or self.motion["Move"].length <= 0.5:
						mx = 0.03*slope
						if wall < 150:
							self.doAnim(NAME="Walking", FRAME=(0,59), PRIORITY=3, MODE="LOOP", BLEND=10)
						else:
							self.doAnim(NAME="Jumping", FRAME=(0+invck,0+invck), PRIORITY=3, MODE="LOOP", BLEND=10)
					else:
						mx = self.data["SPEED"]*slope
						if wall < 160:
							self.doAnim(NAME="Running", FRAME=(0,39), PRIORITY=3, MODE="LOOP", BLEND=10)
						else:
							self.doAnim(NAME="Jumping", FRAME=(0+invck,0+invck), PRIORITY=3, MODE="LOOP", BLEND=10)

					if self.ACCEL > 1:
						mx = mx*(self.motion["Accel"]/self.ACCEL)
						if self.motion["Accel"] < self.ACCEL:
							self.motion["Accel"] += 1

					mref = dref.copy()*mx
					owner.worldPosition[0] += mref[0]
					owner.worldPosition[1] += mref[1]

				else:
					self.motion["Accel"] = 0
					self.doAnim(NAME="Jumping", FRAME=(0+invck,0+invck), PRIORITY=3, MODE="LOOP", BLEND=10)

			elif self.jump_state == "JUMP":
				self.jump_timer += 1
				if self.jump_timer > 10 and owner.localLinearVelocity[2] < 0.1:
					self.doAnim(NAME="KO", FRAME=(0,60), PRIORITY=2, MODE="PLAY", BLEND=5)
					owner.setDamping(1.0, 1.0)
					owner.applyForce((0,0,-1*scene.gravity[2]), False)
					owner.worldPosition[2] = ground[1][2]+1
				if self.jump_timer > 60:
					self.jump_timer = 0
					self.jump_state = "NONE"

			elif self.jump_state in ["FALLING", "A_JUMP", "B_JUMP"] and owner.localLinearVelocity[2] < 2:
				owner.setDamping(1.0, 1.0)
				self.jump_timer = 0
				self.jump_state = "NONE"
				if self.motion["Move"].length > 0.01:
					self.motion["Accel"] = self.ACCEL
				else:
					self.motion["Accel"] = 0

		elif self.jump_state == "EDGE":
			self.ST_Hanging_Set()
			return

		else:
			self.doAnim(NAME="Jumping", FRAME=(40,40), PRIORITY=3, MODE="LOOP", BLEND=10)
			owner.setDamping(0.3, 0.3)
			self.jump_timer += 1

			if self.jump_state in ["FALLING", "A_JUMP", "B_JUMP"]:
				if self.motion["Move"].length > 0.01:
					vref = self.objects["VertRef"].getAxisVect((move[0], move[1], 0))
					owner.applyForce((vref[0]*5, vref[1]*5, 0), False)

			if self.jump_state in ["NONE", "JUMP"]:
				if self.jump_state == "NONE" and not keymap.BINDS["PLR_DUCK"].active() == True:
					owner.localLinearVelocity = (0,1,1)
				self.jump_state = "A_JUMP"

			if keymap.BINDS["PLR_JUMP"].active() == True:
				if self.jump_state == "FALLING":
					self.jump_state = "B_JUMP"
			else:
				self.jump_state = "FALLING"

		owner.alignAxisToVect((0,0,1), 2, 1.0)

		self.objects["Character"]["DEBUG1"] = self.rayorder
		self.objects["Character"]["DEBUG2"] = str(self.jump_state)

		self.doInteract()
		self.checkStability()
		self.weaponManager()

		if keymap.BINDS["TOGGLEMODE"].tap() == True:
			self.ST_Advanced_Set()

	def ST_Walking_Set(self):
		self.doAnim(STOP=True)
		self.active_state = self.ST_Walking

	## EDGE HANG STATE ##
	def ST_Hanging_Set(self):
		self.objects["Root"].setDamping(1.0, 1.0)
		self.objects["Root"].localLinearVelocity = (0,0,0)

		#self.jump_state = "HANG"
		self.jump_timer = 0
		self.motion["Accel"] = 0
		self.data["HUD"]["Target"] = None

		self.active_state = self.ST_Hanging

	def ST_Hanging(self):
		owner = self.objects["Root"]

		self.doAnim(NAME="EdgeClimb", FRAME=(0,0), MODE="LOOP", BLEND=5)

		owner.applyForce((0,0,-1*owner.scene.gravity[2]), False)
		owner.worldPosition = self.rayorder[0]

		if keymap.BINDS["PLR_JUMP"].tap() == True:
			self.ST_EdgeClimb_Set()

		if keymap.BINDS["PLR_DUCK"].active() == True:
			self.ST_EdgeFall_Set()

	def ST_EdgeClimb_Set(self):
		owner = self.objects["Root"]
		dist = owner.getDistanceTo(self.rayorder[1])

		SH = owner.rayCastTo(self.rayorder[1], dist+1, "GROUND")

		if SH == None:
			self.doAnim(STOP=True)
			self.doAnim(NAME="EdgeClimb", FRAME=(0,60), MODE="PLAY")
			self.objects["Root"].suspendDynamics()
			#self.jump_state = "CLIMB"
			self.jump_timer = 0
			self.active_state = self.ST_EdgeClimb

	def ST_EdgeClimb(self):
		owner = self.objects["Root"]

		time = 60
		start = self.createVector(vec=self.rayorder[0])
		end = self.createVector(vec=self.rayorder[1])

		self.jump_timer += 1

		owner.applyForce((0,0,-1*owner.scene.gravity[2]), False)
		owner.worldPosition = start.lerp(end, self.jump_timer/time)

		if self.jump_timer == time:
			self.objects["Root"].restoreDynamics()
			self.rayorder = "NONE"
			self.jump_state = "NONE"
			self.jump_timer = 0
			self.doAnim(STOP=True)
			self.active_state = self.ST_Walking

	def ST_EdgeFall_Set(self):
		self.rayorder = "NONE"
		self.jump_state = "FALLING"
		self.jump_timer = 0
		self.doAnim(STOP=True)
		self.active_state = self.ST_Walking

	## FLY STATE ##
	def ST_FlySimple(self):
		scene = base.SC_SCN
		owner = self.objects["Root"]

		self.alignPlayer(0.5)

		mx = 10
		move = self.motion["Move"]
		climb = self.motion["Climb"]

		owner.applyForce((0,0,-1*scene.gravity[2]), False)
		owner.applyForce((move[0]*mx, move[1]*mx, climb*mx), True)

		self.doAnim(NAME="Jumping", FRAME=(40,40), PRIORITY=3, MODE="LOOP", BLEND=10)

		if keymap.BINDS["TOGGLEMODE"].tap() == True:
			self.jump_state = "FALLING"
			self.ST_Walking_Set()

	def ST_Advanced_Set(self):
		self.jump_state = "FLYING"
		self.objects["Root"].setDamping(0.5, 0.5)
		self.data["HUD"]["Target"] = None
		self.active_state = self.ST_FlySimple

	## RUN ##
	def RUN(self):
		if self.objects["Root"] == None:
			return
		self.runPre()
		self.getInputs()
		self.doCameraState()
		self.doCameraCollision()
		self.runStates()
		self.runPost()



