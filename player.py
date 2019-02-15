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


from bge import logic, render

from . import keymap, base, HUD, config, viewport




class ActorLayout(HUD.HUDLayout):

	GROUP = "Core"
	MODULES = [
		HUD.Stats,	# Health Bars
		HUD.Interact,	# Target and Text
		HUD.Inventory,	# Number Slots and Side Icons
		HUD.Weapons,	# Top Center Indicator
		HUD.Compass
		]


class CorePlayer(base.CoreAdvanced):

	NAME = "Player"
	PHYSICS = "Player"
	PORTAL = True
	GHOST = True
	CLASS = "Standard"
	WP_TYPE = "RANGED"

	HAND = {"MAIN":"Hand_R", "OFF":"Hand_L"}
	SLOTS = {"THREE":"Hip_L", "FOUR":"Shoulder_L", "FIVE":"Back", "SIX":"Shoulder_R", "SEVEN":"Hip_R"}

	SPEED = 0.1
	JUMP = 6
	ACCEL = 30
	SLOPE = 60
	MOVERUN = True
	SIDESTEP = False
	GRAV_DAMAGE = 10

	INTERACT = 2
	EYE_H = 1.6
	GND_H = 1.0
	EDGE_H = 2.0
	WALL_DIST = 0.4
	OFFSET = (0, 0.0, 0.2)

	CAM_ORBIT = 2
	CAM_SLOW = 10
	CAM_RANGE = (0.75,6)
	CAM_HEIGHT = 0.15
	CAM_STEPS = 7
	CAM_ZOOM = 2
	CAM_MIN = 0.2

	HUDLAYOUT = ActorLayout

	def __init__(self):
		scene = base.SC_SCN
		char = logic.getCurrentController().owner

		self.objects = {"Root":None, "Character":char}

		self.findObjects(char)

		self.ANIMOBJ = self.objects["Rig"]

		self.defaultStates()

		self.gndraybias = self.GND_H
		self.wallraydist = self.WALL_DIST
		self.wallrayto = self.createVector(vec=(0, self.WALL_DIST, 0))
		self.wallrayup = self.createVector(vec=(0, self.WALL_DIST, self.EDGE_H-self.GND_H+0.3))

		self.jump_state = "NONE"
		self.jump_timer = 0
		self.crouch = 0
		self.rayorder = "NONE"
		self.lastaction = [None,0]

		self.rayhit = None
		self.rayvec = None

		self.groundhit = None
		self.groundobj = None
		self.groundchk = False
		self.groundpos = [self.createVector(), self.createVector()]
		self.groundori = [self.createMatrix(), self.createMatrix()]

		self.motion = {"Move":self.createVector(2), "Rotate":self.createVector(3), "Climb":0, "Accel":0}

		self.data = {"HEALTH":100, "ENERGY":100, "RECHARGE":0.01, "SPEED":self.SPEED,
			"JUMP":self.JUMP, "RUN":self.MOVERUN, "STRAFE":self.SIDESTEP}

		self.data["HUD"] = {"Text":"", "Color":(0,0,0,0.5), "Target":None, "Locked":None}

		self.data["DAMPING"] = [0, 0]
		self.data["LINVEL"] = [0,0,0]
		self.data["PHYSICS"] = "DYNAMIC"
		self.data["CROUCH"] = self.crouch
		self.data["JP_STATE"] = self.jump_state
		self.data["JP_TIMER"] = self.jump_timer
		self.data["GB_STATE"] = self.rayorder

		dict = self.defaultData()
		for key in dict:
			if key not in self.data:
				self.data[key] = dict[key]

		char["Class"] = self
		char["DEBUG1"] = ""
		char["DEBUG2"] = ""
		char["RAYTEXT"] = ""
		char.addDebugProperty("DEBUG1", True)
		char.addDebugProperty("DEBUG2", True)
		char.addDebugProperty("RAYTEXT", True)

		keymap.MOUSELOOK.center()

		self.doLoad()
		self.loadInventory(char)

		if logic.PLAYERCLASS == None:
			logic.PLAYERCLASS = self
			HUD.SetBlackScreen(True)

			if base.DATA["Portal"]["Vehicle"] != None:
				dict = base.DATA["Portal"]["Vehicle"]
				vehicle = scene.addObject(dict["Object"], base.SC_RUN, 0)
				vehicle["DICT"] = dict
				vehicle["RAYCAST"] = self

			else:
				owner = self.addPhysicsBox()
				self.findObjects(owner)
				self.parentArmature(owner)

				self.assignCamera(load=True)

				self.doPortal()

				HUD.SetLayout(self)

				self.doPlayerAnim("IDLE.RESET")

		self.ST_Startup()

	def defaultStates(self):
		self.active_pre = []
		self.active_state = self.ST_Walking
		self.active_post = [self.PS_Recharge, self.PS_GroundTrack]

	def doPortal(self):
		scene = base.SC_SCN
		owner = self.objects["Root"]

		door = base.DATA["Portal"]["Door"]
		zone = base.DATA["Portal"]["Zone"]
		portal = scene.objects.get(str(door), None)

		if portal != None:
			pos = portal.worldPosition.copy()
			ori = portal.worldOrientation.copy()

			if zone != None:
				pos = self.createVector(vec=zone[0])
				pos = portal.worldPosition+(portal.worldOrientation*pos)

				ori = ori*self.createMatrix(mat=zone[1])

			owner.worldPosition = pos
			owner.worldOrientation = ori

		elif "POS" in base.LEVEL["PLAYER"]:
			owner.worldPosition = base.LEVEL["PLAYER"]["POS"]
			owner.worldOrientation = base.LEVEL["PLAYER"]["ORI"]

		else:
			base.LEVEL["PLAYER"]["POS"] = self.vecTuple(owner.worldPosition)
			base.LEVEL["PLAYER"]["ORI"] = self.matTuple(owner.worldOrientation)

		if portal != None and zone == None:
			self.data["CAMERA"]["ZR"] = [0,0,0]
			self.data["CAMERA"]["XR"] = 0

		owner.localLinearVelocity = self.data["LINVEL"]

		viewport.updateCamera(self, owner, load=True)

		if base.DATA["Portal"]["Vehicle"] == None or portal == None:
			base.DATA["Portal"]["Door"] = None
			base.DATA["Portal"]["Zone"] = None

	def doLoad(self):
		if self.NAME in base.PROFILE["PLRData"]:
			self.data = base.PROFILE["PLRData"][self.NAME]
			self.active_state = getattr(self, self.data["ACTIVE_STATE"])
		else:
			base.PROFILE["PLRData"][self.NAME] = self.data
			self.data["ACTIVE_STATE"] = self.active_state.__name__


		self.jump_state = self.data["JP_STATE"]
		self.jump_timer = self.data["JP_TIMER"]
		self.rayorder = self.data["GB_STATE"]
		self.crouch = self.data["CROUCH"]

		if self not in logic.UPDATELIST:
			logic.UPDATELIST.append(self)

	def doUpdate(self):

		self.data["JP_STATE"] = self.jump_state
		self.data["JP_TIMER"] = self.jump_timer
		self.data["GB_STATE"] = self.rayorder
		self.data["CROUCH"] = self.crouch
		self.data["ACTIVE_STATE"] = self.active_state.__name__

		owner = self.objects["Root"]
		if owner == None:
			return

		self.data["LINVEL"] = self.vecTuple(owner.localLinearVelocity)
		self.data["DAMPING"] = [owner.linearDamping, owner.angularDamping]

		base.LEVEL["PLAYER"]["POS"] = self.vecTuple(owner.worldPosition)
		base.LEVEL["PLAYER"]["ORI"] = self.matTuple(owner.worldOrientation)

	def addPhysicsBox(self):
		char = self.objects["Character"]

		owner = char.scene.addObject(self.PHYSICS, char, 0)
		owner.setDamping(self.data["DAMPING"][0], self.data["DAMPING"][1])
		owner["Class"] = self

		self.objects["Root"] = owner

		self.addCollisionCallBack()
		self.setPhysicsType()

		return owner

	def parentArmature(self, obj, offset=False):
		char = self.objects["Character"]

		if offset == True:
			POS = self.OFFSET
		else:
			POS = (0,0,0)

		if char.parent != obj:
			char.setParent(obj)

		char.localPosition = POS
		char.localOrientation = self.createMatrix()

	def assignCamera(self, load=False):
		viewport.setCamera(self, load)
		viewport.setParent(self.objects["Root"])
		if self.data["CAMERA"]["State"] == "THIRD":
			viewport.setEyeHeight(self.EYE_H-self.GND_H, set=load)
		elif self.data["CAMERA"]["State"] == "SHOULDER":
			viewport.setEyeHeight(
				eye = [self.CAM_SHSIDE, 0, self.EYE_H-self.GND_H-self.CAM_MIN],
				set = load)

	def enterVehicle(self, seat):
		self.jump_state = "NONE"
		self.jump_timer = 0
		self.crouch = 0
		self.rayorder = "NONE"
		self.data["HUD"]["Target"] = None
		self.data["HUD"]["Text"] = ""

		#self.doUpdate(False)

		if self.objects["Root"] != None:
			self.doCrouch(False)
			self.objects["Character"].removeParent()
			self.objects["Root"].endObject()
			self.objects["Root"] = None

		self.parentArmature(seat, True)

	def exitVehicle(self, spawn):
		keymap.MOUSELOOK.center()

		self.doPlayerAnim("IDLE.RESET")

		self.objects["Character"].removeParent()
		self.objects["Character"].setVisible(True, True)

		owner = self.addPhysicsBox()
		owner.alignAxisToVect((0,0,1), 2, 1.0)
		owner.worldPosition = spawn

		self.findObjects(owner)
		self.parentArmature(owner)
		self.assignCamera()

		HUD.SetLayout(self)

	def switchPlayerPassive(self):
		self.jump_state = "NONE"
		self.jump_timer = 0
		self.crouch = 0
		self.rayorder = "NONE"
		self.data["HUD"]["Target"] = None
		self.data["HUD"]["Text"] = ""

		#self.doUpdate(False)

		if self.objects["Root"] != None:
			self.doCrouch(False)
			self.objects["Character"].removeParent()
			self.objects["Root"].endObject()
			self.objects["Root"] = None

		self.doPlayerAnim("IDLE.RESET")

	def switchPlayerActive(self):
		keymap.MOUSELOOK.center()

		self.doAnim(STOP=True)

		owner = self.addPhysicsBox()

		self.findObjects(owner)
		self.parentArmature(owner)
		self.assignCamera(load=True)

		HUD.SetLayout(self)

		logic.PLAYERCLASS = self
		base.CURRENT["Player"] = self.objects["Character"].name

	def alignCamera(self, factor=1.0, axis=(0,1,0), up=(0,0,1)):
		vref = self.objects["Root"].getAxisVect(axis)
		viewport.setDirection(vref, factor)

	def alignPlayer(self, factor=1.0, axis=None, up=(0,0,1)):
		if axis == None:
			axis = viewport.getDirection()
		self.objects["Root"].alignAxisToVect(axis, 1, factor)
		self.objects["Root"].alignAxisToVect(up, 2, 1.0)

	def getDropPoint(self):
		drop = viewport.getRayVec()*(self.INTERACT-0.5)
		drop += self.objects["Root"].worldPosition

		if self.rayhit != None:
			if self.rayvec.length < self.INTERACT:
				drop = self.rayhit[1]+(self.rayhit[2]*0.5)

		return list(drop)

	def getInputs(self):

		FORWARD = keymap.BINDS["PLR_FORWARD"].axis() - keymap.BINDS["PLR_BACKWARD"].axis()
		STRAFE = keymap.BINDS["PLR_STRAFERIGHT"].axis() - keymap.BINDS["PLR_STRAFELEFT"].axis()
		MOVE = keymap.input.JoinAxis(STRAFE, FORWARD)
		CLIMB = 0

		TURN = keymap.BINDS["PLR_TURNLEFT"].axis() - keymap.BINDS["PLR_TURNRIGHT"].axis()
		LOOK = keymap.BINDS["PLR_LOOKUP"].axis() - keymap.BINDS["PLR_LOOKDOWN"].axis()
		ROTATE = keymap.input.JoinAxis(LOOK, 0, TURN)

		## Key Commands ##
		if keymap.BINDS["PLR_FORWARD"].active() == True:
			MOVE[1] = 1

		if keymap.BINDS["PLR_BACKWARD"].active() == True:
			MOVE[1] = -1

		if keymap.BINDS["PLR_STRAFERIGHT"].active() == True:
			MOVE[0] = 1

		if keymap.BINDS["PLR_STRAFELEFT"].active() == True:
			MOVE[0] = -1

		if keymap.BINDS["PLR_TURNLEFT"].active() == True:
			ROTATE[2] += 1

		if keymap.BINDS["PLR_TURNRIGHT"].active() == True:
			ROTATE[2] -= 1

		if keymap.BINDS["PLR_LOOKUP"].active() == True:
			ROTATE[0] += 1

		if keymap.BINDS["PLR_LOOKDOWN"].active() == True:
			ROTATE[0] -= 1

		if keymap.BINDS["PLR_JUMP"].active() == True:
			CLIMB = 1

		if keymap.BINDS["PLR_DUCK"].active() == True:
			CLIMB = -1

		self.motion["Move"][0] = MOVE[0]
		self.motion["Move"][1] = MOVE[1]
		self.motion["Climb"] = CLIMB

		self.motion["Rotate"][0] = ROTATE[0]
		self.motion["Rotate"][1] = 0
		self.motion["Rotate"][2] = ROTATE[2]

		if keymap.BINDS["PLR_RUN"].tap() == True:
			self.data["RUN"] ^= True

		if self.data["CAMERA"]["State"] == "THIRD":
			if keymap.BINDS["TOGGLESTRAFE"].tap() == True:
				self.data["STRAFE"] ^= True

			if keymap.BINDS["TOGGLECAM"].tap() == True:
				viewport.setState("SHOULDER")
				viewport.setEyeHeight(eye=[self.CAM_SHSIDE,0,self.EYE_H-self.GND_H-self.CAM_MIN])
				#self.data["CAMERA"]["FOV"] = 60

		elif self.data["CAMERA"]["State"] == "SHOULDER":
			if keymap.BINDS["TOGGLECAM"].tap() == True:
				viewport.setState("THIRD")
				viewport.setEyeHeight(self.EYE_H-self.GND_H)
				#self.data["CAMERA"]["FOV"] = self.CAM_FOV

		for slot in self.data["SLOTS"]:
			key = self.data["SLOTS"][slot]
			if slot in self.cls_dict and keymap.BINDS[key].tap() == True:
				cls = self.cls_dict[slot]
				if keymap.SYSTEM["ALT"].checkModifiers() == True:
					cls.dropItem(self.getDropPoint())
				else:
					cls.stateSwitch(run=True)

		if keymap.BINDS["SUPER_DROP"].tap() == True:
			WPDROP = self.getDropPoint()
			for slot in list(self.data["INVSLOT"].keys()):
				self.cls_dict[slot].dropItem(WPDROP)
				WPDROP[2] += 2
			for slot in list(self.data["WEAPSLOT"].keys()):
				self.cls_dict[slot].dropItem(WPDROP)
				WPDROP[2] += 2

	def setPhysicsType(self, mode=None):
		owner = self.objects["Root"]

		if mode == None:
			mode = self.data["PHYSICS"]

		if mode == "NONE":
			owner.disableRigidBody()
			owner.suspendDynamics()
		else:
			owner.restoreDynamics()
			if mode == "RIGID":
				owner.enableRigidBody()
			else:
				owner.disableRigidBody()

		self.data["PHYSICS"] = mode

	def getGroundPoint(self, obj):
		if self.groundchk == True:
			print("WARNING: Ground reference already updated...")
			return

		newpos = obj.worldPosition.copy()
		newori = obj.worldOrientation.copy()

		self.groundpos.insert(0, newpos)
		self.groundpos.pop()
		self.groundori.insert(0, newori)
		self.groundori.pop()

		self.groundchk = True

		if self.groundobj != obj:
			self.groundobj = obj
			self.groundpos[1] = self.groundpos[0].copy()
			self.groundori[1] = self.groundori[0].copy()

	def checkWall(self, z=True, axis=None, simple=None, prop="GROUND"):
		owner = self.objects["Root"]

		if axis == None:
			axis = owner.getAxisVect((0,1,0))
		else:
			axis = self.createVector(vec=axis)
		dist = self.WALL_DIST+0.3
		angle = -1

		if simple != None:
			dist = simple

		WALLOBJ, WALLPNT, WALLNRM = owner.rayCast(owner.worldPosition+axis, None, dist, prop, 1, 0, 0)

		if WALLOBJ != None:
			if simple != None:
				return WALLOBJ, WALLPNT, WALLNRM
			if z == False:
				WALLNRM[2] = 0
				WALLNRM.normalize()
			if WALLNRM.length > 0.01:
				angle = axis.angle(WALLNRM, 0)
				angle = round(self.toDeg(angle), 2)

		else:
			if simple != None:
				return None

		return angle, WALLNRM

	def checkEdge(self, simple=False):
		owner = self.objects["Root"]
		rayup = self.getWorldSpace(owner, self.wallrayup)
		rayto = self.getWorldSpace(owner, self.wallrayto)

		#if owner.get("XX", None) == None:
		#	owner["XX"] = owner.scene.addObject("Gimbal", owner, 0)
		#	owner["XX"].setParent(owner)

		#guide = owner["XX"]

		EDGEOBJ, EDGEPNT, EDGENRM = owner.rayCast(rayto, rayup, self.EDGE_H+0.6, "GROUND", 1, 1, 0)

		if simple == True:
			if EDGEOBJ == None:
				return None

		#	guide.worldPosition = EDGEPNT
			angle = self.createVector(vec=[0,0,1]).angle(EDGENRM, 0)
			angle = round(self.toDeg(angle), 2)

			if angle > self.SLOPE:
				return None

			return EDGEOBJ, EDGEPNT, EDGENRM

		CHK = owner.rayCastTo(rayup, 0, "GROUND")

		if EDGEOBJ != None and CHK == None:
		#	guide.worldPosition = EDGEPNT
			angle = self.createVector(vec=[0,0,1]).angle(EDGENRM, 0)
			angle = round(self.toDeg(angle), 2)
			dist = EDGEPNT[2]-owner.worldPosition[2]
			offset = self.EDGE_H-self.GND_H

			if self.rayorder == "END":
				ledge = (EDGEPNT[2]-offset)-owner.worldPosition[2]
				if abs(ledge) > 0.11:
					self.rayorder = "NONE"

			## Vault ##
			if dist > -0.5 and dist < 0.3: # and self.jump_state == "NONE":
				if self.motion["Move"].length > 0.01 and keymap.BINDS["PLR_JUMP"].tap() == True:
					if self.jump_state == "NONE" and dist < -0.5:
						pass
					elif owner.localLinearVelocity.length > -0.01 and self.jump_state in ["NONE","FALLING"]:
						self.motion["Accel"] = 0
						owner.worldPosition = [EDGEPNT[0], EDGEPNT[1], EDGEPNT[2]+1]
						self.jump_state = "FALLING"
						self.doPlayerAnim("JUMP")

			## Ledge Grab ##
			if owner.localLinearVelocity[2] < 0 and self.rayorder == "GRAB" and self.jump_state == "FALLING":
				if angle > self.SLOPE or abs(dist-offset) > 0.1:
					self.rayorder = "GRAB"
				else:
					WP = owner.worldPosition
					WP = [WP[0], WP[1], EDGEPNT[2]-offset]
					RP = [EDGEPNT[0], EDGEPNT[1], EDGEPNT[2]+self.GND_H]
					self.rayorder = [WP, RP]
					self.jump_state = "EDGE"

		else:
		#	guide.worldPosition = rayup-self.createVector(vec=[0,0,self.EDGE_H+0.6])
			if self.rayorder == "END":
				self.rayorder = "NONE"
			if self.jump_state == "EDGE":
				self.rayorder = "NONE"
				self.jump_state = "FALLING"

	def checkGround(self, simple=False, ray=None):
		owner = self.objects["Root"]
		ground = None
		angle = 0
		slope = 1.0
		offset = self.GND_H
		gndto = owner.getAxisVect((0,0,-1))+owner.worldPosition
		gndbias = 0

		if ray == None:
			ray = (gndto, None, offset)

		rayOBJ, rayPNT, rayNRM = owner.rayCast(ray[0], ray[1], ray[2]+0.3, "GROUND", 1, 1, 0)

		if rayOBJ == None:
			self.gndraybias = offset

			if simple == True:
				return None

			if self.rayorder == "NONE":
				self.rayorder = "GRAB"

		else:
			ground = [rayOBJ, rayPNT, rayNRM]

			angle = owner.getAxisVect((0,0,1)).angle(rayNRM, 0)
			angle = round(self.toDeg(angle), 2)
			gndbias = (angle/90)*0.3

			if self.jump_state not in ["NONE", "CROUCH"]:
				if owner.worldPosition[2]-rayPNT[2] > offset+gndbias:
					ground = None
				else:
					self.gndraybias = offset+gndbias

			if simple == True:
				self.gndraybias = offset+gndbias
				return ground

			if angle > self.SLOPE:
				ground = None

		if ground != None:
			if angle > 5 and angle < 90:
				rayNRM[2] = 0
				rayNRM = rayNRM.normalized()
				dot = owner.getAxisVect((0,1,0)).angle(rayNRM, 0)/1.571
				slope = 1-(abs(dot-1)*((angle/90)))

			self.getGroundPoint(rayOBJ)

			self.rayorder = "NONE"

			self.groundhit = ground
			self.gndraybias += ((offset+gndbias)-self.gndraybias)*0.2

		return ground, angle, slope

	def doInteract(self):
		scene = base.SC_SCN
		owner = self.objects["Root"]

		rayfrom = self.getWorldSpace(owner, (0,0,self.EYE_H-self.GND_H))
		rayto = rayfrom+viewport.getRayVec()
		dist = 200

		if self.data["CAMERA"]["State"] == "SHOULDER":
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
			self.rayvec = rayfrom-RAYHIT[1]

			screen = scene.active_camera.getScreenPosition(RAYHIT[1])
			RAYTARGPOS[0] = screen[0]
			RAYTARGPOS[1] = screen[1]

			if self.rayvec.length < self.INTERACT:
				RAYOBJ = RAYHIT[0]

				if self.rayvec.dot(RAYHIT[2]) < 0 and config.DO_STABILITY == True:
					RAYCOLOR = (0,0,1,1)
					self.data["HUD"]["Text"] = "Press "+keymap.BINDS["ACTIVATE"].input_name+" To Ghost Jump"
					if keymap.BINDS["ACTIVATE"].tap() == True:
						owner.worldPosition = RAYHIT[1]+(RAYHIT[2]*self.WALL_DIST)
				elif "RAYCAST" in RAYOBJ:
					if self.active_weapon != None:
						RAYCOLOR = (1,0,0,1)
					else:
						RAYCOLOR = (0,1,0,1)
						RAYOBJ["RAYCAST"] = self

				if RAYOBJ.get("RAYNAME", None) != None:
					self.data["HUD"]["Text"] = RAYOBJ["RAYNAME"]

		if self.groundhit != None:
			if "RAYFOOT" in self.groundhit[0]:
				self.groundhit[0]["RAYFOOT"] = self

		self.data["HUD"]["Color"] = RAYCOLOR
		self.data["HUD"]["Target"] = RAYTARGPOS

	def doJump(self, height=None, move=0.5):
		owner = self.objects["Root"]

		self.jump_state = "JUMP"
		self.jump_timer = 0

		#self.motion["Accel"] = 0

		owner.setDamping(0, 0)

		if height == None:
			height = self.data["JUMP"]

		align = owner.worldLinearVelocity.copy()
		align[2] = 0
		if align.length > 0.01 and move > 0:
			if self.data["STRAFE"] == False and self.data["CAMERA"]["State"] == "THIRD":
				self.alignPlayer(axis=align)

		owner.worldLinearVelocity[0] *= move
		owner.worldLinearVelocity[1] *= move

		owner.worldLinearVelocity[2] = height

		self.doPlayerAnim("JUMP", 5)

	def doMovement(self, vec, mx=0, local=False):
		owner = self.objects["Root"]

		axis = vec
		if local == True:
			axis = (0,1,0)

		vref = viewport.getDirection(axis)
		dref = owner.getAxisVect((0,1,0))
		dot = 1-((vref.dot(dref)*0.5)+0.5)
		dot = 0.2+((dot**2)*0.5)

		owner.alignAxisToVect(vref, 1, dot)

		if mx <= 0:
			return

		if self.ACCEL > 1:
			mx *= (self.motion["Accel"]/self.ACCEL)
			if self.motion["Accel"] < self.ACCEL:
				self.motion["Accel"] += 1

		mref = vref.copy()
		if local == True:
			mref = viewport.getDirection(vec)

		owner.worldLinearVelocity[0] = (mref[0]*mx)*60
		owner.worldLinearVelocity[1] = (mref[1]*mx)*60

	def doPlayerAnim(self, action="IDLE", blend=10):

		if action == "JUMP":
			self.doAnim(NAME="Jumping", FRAME=(0,20), PRIORITY=2, MODE="PLAY", BLEND=10)
			self.lastaction = [action, 0]
			return

		if action == "FALLING":
			self.doAnim(NAME="Jumping", FRAME=(40,40), PRIORITY=3, MODE="LOOP", BLEND=blend)
			self.lastaction = [action, 0]
			return

		move = action.split(".")

		if "IDLE" in move:
			invck = 0
			for slot in self.cls_dict:
				if slot in ["Hip_L", "Hip_R"]:
					invck = -5

			if "RESET" in move:
				self.doAnim(NAME="Jumping", FRAME=(0+invck,0+invck))
			else:
				self.doAnim(NAME="Jumping", FRAME=(0+invck,0+invck), PRIORITY=3, MODE="LOOP", BLEND=blend)
			self.lastaction = [action, 0]
			return

		if "STAIR" in move:
			stair = ".Stairs"
		else:
			stair = ""

		setframe = 0

		if move[0] == "FORWARD":
			if "WALK" in move:
				self.doAnim(NAME="Walking", FRAME=(0,59), PRIORITY=3, MODE="LOOP", BLEND=blend)
				setframe = 59
			else:
				self.doAnim(NAME="Running"+stair, FRAME=(0,39), PRIORITY=3, MODE="LOOP", BLEND=blend)
				setframe = 39

		elif move[0] == "BACKWARD":
			if "WALK" in move:
				self.doAnim(NAME="Walking", FRAME=(59,0), PRIORITY=3, MODE="LOOP", BLEND=blend)
				setframe = 59
			else:
				self.doAnim(NAME="Running"+stair, FRAME=(39,0), PRIORITY=3, MODE="LOOP", BLEND=blend)
				setframe = 39

		else:
			self.lastaction = ["IDLE", 0]
			self.doPlayerAnim("IDLE")
			return

		if self.lastaction[0] != action:
			self.lastaction[0] = action
			self.doAnim(SET=self.lastaction[1]*setframe)
		if setframe != 0:
			self.lastaction[1] = self.doAnim(CHECK="FRAME")/setframe

	def doCrouch(self, state):
		self.motion["Accel"] = 0
		if state == True or self.crouch != 0:
			self.jump_state = "CROUCH"
			self.objects["Root"].localScale[2] = 0.25
			self.objects["Character"].localScale[2] = 4
			self.active_state = self.ST_Crouch
		elif state == False:
			self.jump_state = "NONE"
			self.objects["Root"].localScale[2] = 1
			self.objects["Character"].localScale[2] = 1
			self.active_state = self.ST_Walking
			if self.data["CAMERA"]["State"] == "THIRD":
				viewport.setEyeHeight(self.EYE_H-self.GND_H)

	## INIT STATE ##
	def ST_Startup(self):
		if self.jump_state == "FLYING" and self.objects["Root"] != None:
			self.ST_Advanced_Set()

	## POST ##
	def PS_Recharge(self):
		if self.data["HEALTH"] < 0:
			self.data["HEALTH"] = -1
		if self.data["ENERGY"] < 100:
			self.data["ENERGY"] += self.data["RECHARGE"]
			if self.data["ENERGY"] > 100:
				self.data["ENERGY"] = 100

	def PS_GroundTrack(self):
		owner = self.objects["Root"]
		self.groundchk = False

		if self.groundhit == None or self.jump_state not in ["NONE", "CROUCH", "JUMP", "HANGING"]:
			dragX = owner.worldLinearVelocity[0]*0.67
			dragY = owner.worldLinearVelocity[1]*0.67
			dragZ = owner.worldLinearVelocity[2]*0.33
			owner.applyForce((-dragX, -dragY, -dragZ), False)
			self.groundhit = None
			self.groundobj = None
			return

		rayOBJ = self.groundobj

		locOLD = owner.worldPosition - self.groundpos[1]
		posOLD = self.groundori[1].inverted()*locOLD

		locNEW = owner.worldPosition - self.groundpos[0]
		posNEW = self.groundori[0].inverted()*locNEW

		local = posOLD - posNEW
		offset = self.groundori[0]*local

		if self.data["PHYSICS"] == "NONE":
			#owner.worldPosition[0] += offset[0]
			#owner.worldPosition[1] += offset[1]
			owner.applyMovement((offset[0], offset[1], 0), False)
		else:
			owner.worldLinearVelocity[0] += offset[0]*60
			owner.worldLinearVelocity[1] += offset[1]*60

		yvec = owner.getAxisVect((0,1,0))
		rotOLD = self.groundori[1].inverted()*yvec
		rotOLD = self.groundori[0]*rotOLD
		euler = yvec.rotation_difference(rotOLD).to_euler()

		owner.applyRotation((0,0,euler[2]), True)

		owner.applyForce(-owner.scene.gravity, False)

		self.groundhit = None

	## WALKING STATE ##
	def ST_Crouch(self):
		scene = base.SC_SCN
		owner = self.objects["Root"]
		char = self.objects["Character"]

		owner.localScale[2] = 0.25
		char.localScale[2] = 4

		cr_fac = 1-(self.crouch*0.04)

		ground, angle, slope = self.checkGround()

		owner.setDamping(0, 0)

		if ground != None:
			owner.worldLinearVelocity = (0,0,0)
			owner.worldPosition[2] = ground[1][2] + (self.gndraybias*cr_fac)

			if ground[0].getPhysicsId() != 0:
				impulse = scene.gravity*owner.mass*0.1
				ground[0].applyImpulse(ground[1], impulse, False)

			point = ground[1][2]+2
			dist = abs(point-owner.worldPosition[2])
			chkwall = (self.checkWall(axis=(0,0,1), simple=dist)!=None)
			if keymap.BINDS["PLR_DUCK"].active() == True or self.crouch == 10:
				chkwall = True
				if keymap.BINDS["PLR_DUCK"].released() == True:
					chkwall = False
		else:
			chkwall = False

		if self.motion["Move"].length > 0.01:
			move = self.motion["Move"].normalized()
			self.doMovement((move[0], move[1], 0), 0.02)
		else:
			self.motion["Accel"] = 0

		owner.alignAxisToVect((0,0,1), 2, 1.0)

		self.doInteract()
		self.checkStability()
		self.weaponManager()

		if chkwall == False:
			self.doPlayerAnim("IDLE")
			if self.crouch <= 0:
				self.crouch = 0
				self.doCrouch(False)
				return
			else:
				self.crouch -= 1

		else:
			if self.motion["Move"].length > 0.01:
				self.doAnim(NAME="Crouching", FRAME=(0,80), PRIORITY=3, MODE="LOOP", BLEND=10)
			else:
				self.doAnim(NAME="Crouching", FRAME=(0,0), PRIORITY=3, MODE="LOOP", BLEND=10)

			if self.crouch < 10:
				self.crouch += 1

		if self.data["CAMERA"]["State"] == "THIRD":
			viewport.setEyeHeight( (self.EYE_H-self.GND_H)*cr_fac, set=True)

	def ST_Walking(self):
		scene = base.SC_SCN
		owner = self.objects["Root"]
		char = self.objects["Character"]

		move = self.motion["Move"].normalized()

		ground, angle, slope = self.checkGround()

		self.checkEdge()

		owner.setDamping(0, 0)

		if ground != None:
			if self.jump_state == "NONE":
				owner.worldLinearVelocity = (0,0,0)
				owner.worldPosition[2] = ground[1][2] + self.gndraybias

				strafe = self.data["STRAFE"]
				action = "IDLE"
				blend = 10

				if self.data["CAMERA"]["State"] == "SHOULDER":
					strafe = True

				if keymap.BINDS["PLR_DUCK"].active() == True:
					self.doCrouch(True)

				elif self.motion["Move"].length > 0.01:
					wall, wallnrm = self.checkWall(z=False, axis=viewport.getDirection((move[0], move[1], 0)))

					mx = self.data["SPEED"]*slope

					if self.ACCEL > 10:
						blend = (self.ACCEL+10)-(self.motion["Accel"])

					if wall > 135:
						mx = 0.04*slope
						action = "IDLE"

					elif self.data["RUN"] == False or self.motion["Move"].length <= 0.7 or self.data["SPEED"] <= 0:
						mx = 0.04*slope
						action = "FORWARD"
						if strafe == True:
							if move[1] < 0:
								action = "BACKWARD"
							if move[0] > 0.5 and abs(move[1]) < 0.5:
								action = "STRAFE_R"
							if move[0] < -0.5 and abs(move[1]) < 0.5:
								action = "STRAFE_L"
						action = action+".WALK"

					else:
						action = "FORWARD"
						if strafe == True:
							if move[1] < 0:
								action = "BACKWARD"
							if move[0] > 0.5 and abs(move[1]) < 0.5:
								action = "STRAFE_R"
							if move[0] < -0.5 and abs(move[1]) < 0.5:
								action = "STRAFE_L"

					if angle > 20:
						action = action+".STAIR"

					self.doMovement((move[0], move[1], 0), mx, strafe)

				else:
					if self.data["CAMERA"]["State"] == "SHOULDER":
						self.doMovement((0, 1, 0), 0, True)
						#vref = viewport.getDirection(axis)
						#owner.alignAxisToVect(vref, 1, 0.1)


					self.motion["Accel"] = 0
					action = "IDLE"

				self.doPlayerAnim(action, blend)

				if keymap.BINDS["PLR_JUMP"].tap() == True:
					self.doJump(move=0.8)

				if ground[0].getPhysicsId() != 0:
					impulse = scene.gravity*owner.mass*0.1
					ground[0].applyImpulse(ground[1], impulse, False)

			elif self.jump_state in ["JUMP", "JP_WAIT"]:
				self.jump_state = "JP_WAIT"
				self.jump_timer += 1

				#if self.jump_timer > 10 and owner.localLinearVelocity[2] < 0.1:
				#	self.doAnim(NAME="KO", FRAME=(0,60), PRIORITY=2, MODE="PLAY", BLEND=5)
				#	owner.worldLinearVelocity = (0,0,0)
				#	owner.worldPosition[2] = ground[1][2]+self.gndraybias

				if self.jump_timer > 10:
					self.jump_timer = 0
					self.jump_state = "NONE"

			elif self.jump_state in ["FALLING", "A_JUMP", "B_JUMP", "NO_AIR"] and owner.localLinearVelocity[2] < 2:
				self.jump_timer = 0
				self.jump_state = "NONE"
				if ground[0].getPhysicsId() != 0:
					impulse = (owner.worldLinearVelocity+scene.gravity)*owner.mass*0.1
					ground[0].applyImpulse(ground[1], impulse, False)
				Z = owner.worldLinearVelocity[2]
				if Z < -8:
					self.data["HEALTH"] += (Z+8)*self.GRAV_DAMAGE
				print(Z)
				owner.worldLinearVelocity[2] = 0
				if self.motion["Move"].length < 0.01:
					owner.worldLinearVelocity[0] = 0
					owner.worldLinearVelocity[1] = 0
				#	self.motion["Accel"] = 0

		elif self.jump_state == "EDGE":
			self.ST_Hanging_Set()
			return

		else:
			self.doPlayerAnim("FALLING")
			self.jump_timer += 1

			if self.jump_state in ["FALLING", "A_JUMP", "B_JUMP"]:
				if self.data["CAMERA"]["State"] == "SHOULDER":
					#self.doMovement((0, 1, 0), 0, True)
					vref = viewport.getDirection((0,1,0))
					owner.alignAxisToVect(vref, 1, 0.1)
				if self.motion["Move"].length > 0.01:
					vref = viewport.getDirection((move[0], move[1], 0))
					owner.applyForce((vref[0]*5, vref[1]*5, 0), False)

			if self.jump_state in ["NONE", "JUMP"]:
				if self.jump_state == "NONE" and not keymap.BINDS["PLR_DUCK"].active() == True:
					self.doJump(1, 0.5)
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
		self.checkStability(override=keymap.SYSTEM["STABILITY"].tap())
		self.weaponManager()

		if keymap.BINDS["TOGGLEMODE"].tap() == True:
			self.ST_Advanced_Set()

	def ST_Walking_Set(self):
		self.doAnim(STOP=True)
		self.active_state = self.ST_Walking

	## EDGE HANG STATE ##
	def ST_Hanging_Set(self):
		#self.objects["Root"].setDamping(1.0, 1.0)
		self.objects["Root"].worldLinearVelocity = (0,0,0)
		self.objects["Root"].worldPosition = self.rayorder[0]

		self.jump_state = "HANG_INIT"
		self.jump_timer = 0
		self.motion["Accel"] = 0
		self.data["HUD"]["Target"] = None

		self.active_state = self.ST_Hanging

	def ST_Hanging(self):
		owner = self.objects["Root"]

		owner.worldLinearVelocity = (0,0,0)

		if self.checkGround(simple=True) == None:
			offset = self.EDGE_H-self.GND_H

			ray = (self.getWorldSpace(owner, self.wallrayto), self.getWorldSpace(owner, self.wallrayup), 0.3)
			edge = self.checkGround(simple=True, ray=ray)

			if edge != None:
				if abs(owner.worldPosition[2]-(edge[1][2]-offset)) > 0.1:
					edge = None

			rayfrom = owner.worldPosition+self.createVector(vec=(0,0,offset-0.05))
			rayto = rayfrom.copy()+owner.getAxisVect((0,1,0))

			TROBJ, TRPNT, TRNRM = owner.rayCast(rayto, rayfrom, self.WALL_DIST+0.3, "GROUND", 1, 1, 0)

			X = 0
			if TROBJ != None and self.jump_state == "HANGING" and edge != None:
				TRNRM[2] = 0
				TRNRM.normalize()
				owner.worldPosition = TRPNT+(TRNRM*(self.WALL_DIST-0.05))
				move = self.motion["Move"]
				mref = viewport.getDirection((move[0], move[1], 0))
				mref = owner.worldOrientation.inverted()*mref
				if abs(mref[0]) > 0.5:
					X = 1-(2*(mref[0]<0))
				owner.localLinearVelocity[0] = (X*0.01)*60
				self.alignPlayer(0.5, axis=-TRNRM)

			if edge != None:
				self.groundhit = edge
				self.getGroundPoint(edge[0])

				owner.worldPosition[2] = edge[1][2]-offset

				self.jump_state = "HANGING"

			if abs(X) > 0.01:
				self.doAnim(NAME="EdgeTR", FRAME=(1,60), MODE="LOOP", BLEND=10)
			else:
				self.doAnim(NAME="EdgeClimb", FRAME=(0,0), MODE="LOOP", BLEND=5)

		else:
			edge = None

		if edge == None:
			self.ST_EdgeFall_Set()

		if keymap.BINDS["PLR_DUCK"].active() == True:
			self.ST_EdgeFall_Set()
			self.rayorder = "END"

		elif keymap.BINDS["PLR_JUMP"].tap() == True:
			self.ST_EdgeClimb_Set()

	def ST_EdgeClimb_Set(self):
		owner = self.objects["Root"]

		rayto = self.groundhit[1].copy()
		rayto[2] += 1
		dist = owner.getDistanceTo(rayto)

		SH = owner.rayCastTo(rayto, dist+1, "GROUND")

		if SH == None:
			self.setPhysicsType("NONE")
			self.doAnim(STOP=True)
			self.doAnim(NAME="EdgeClimb", FRAME=(0,60), MODE="PLAY")
			self.rayorder = [self.groundhit[0].worldOrientation.inverted()*(rayto-self.groundhit[0].worldPosition),
				owner.worldOrientation.inverted()*(rayto-owner.worldPosition)]
			self.jump_state = "NONE"
			self.jump_timer = 0
			self.active_state = self.ST_EdgeClimb

	def ST_EdgeClimb(self):
		owner = self.objects["Root"]

		self.jump_state = "NONE"
		self.jump_timer += 1

		owner.worldLinearVelocity = (0,0,0)

		offset = self.EDGE_H-self.GND_H
		time = 60
		fac = self.jump_timer/time

		gvec = (owner.worldOrientation*self.rayorder[1])
		gpnt = (gvec*(1-fac))+owner.worldPosition

		rayto = gpnt.copy()
		rayto[2] -= 1

		ray = (rayto, gpnt, 3)
		ground = self.checkGround(simple=True, ray=ray)

		owner.worldPosition[0] += gvec[0]*(1/time)
		owner.worldPosition[1] += gvec[1]*(1/time)

		if ground != None:
			self.groundhit = ground
			self.getGroundPoint(ground[0])

			owner.worldPosition[2] = (ground[1][2]-offset)+(gvec[2]*fac)

		if self.jump_timer == time or ground == None:
			self.setPhysicsType("DYNAMIC")
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

		owner.setDamping(0.5, 0.5)
		owner.applyForce((0,0,-1*scene.gravity[2]), False)
		owner.applyForce((move[0]*mx, move[1]*mx, climb*mx), True)

		self.doPlayerAnim("FALLING")

		if keymap.BINDS["TOGGLEMODE"].tap() == True:
			self.jump_state = "FALLING"
			self.ST_Walking_Set()

	def ST_Advanced_Set(self):
		self.jump_state = "FLYING"
		self.data["HUD"]["Target"] = None
		self.active_state = self.ST_FlySimple

	## RUN ##
	def RUN(self):
		if self.objects["Root"] == None:
			self.PS_Attachments()
			return
		self.runPre()
		self.getInputs()
		self.runStates()
		self.runPost()



