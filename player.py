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
	ACCEL = 20
	ACCEL_FAST = 10
	ACCEL_STOP = 10
	SLOPE = 60
	MOVERUN = True
	SIDESTEP = False
	AIR_DRAG = (0.67, 0.67, 0.33)
	GRAV_DAMAGE = 10

	INTERACT = 2
	EYE_H = 1.6
	GND_H = 1.0
	EDGE_H = 2.0
	WALL_DIST = 0.4
	OFFSET = (0, 0.0, 0.2)
	SLOPE_SPEED = 1.0
	SLOPE_BIAS = 0.0
	CROUCH_H = 0.4
	CROUCH_SCALE = 0.2 #Capsule is 50% effected by scale

	CAM_TYPE = "FIRST"
	CAM_FOV = 90
	CAM_ORBIT = 2
	CAM_SLOW = 10
	CAM_RANGE = (0.75, 6) #0.75 6
	CAM_HEIGHT = 0.15
	CAM_STEPS = 7
	CAM_ZOOM = 2
	CAM_MIN = 0.2

	HUDLAYOUT = ActorLayout

	def __init__(self):
		scene = base.SC_SCN
		char = logic.getCurrentController().owner

		char["Class"] = self
		char["DICT"] = char.get("DICT", base.PROFILE["PLRData"].get(char.name, {"Object":char.name, "Data":None}))
		char["DICT"]["ID"] = char["DICT"].get("ID", char.get("ID", None))

		self.objects = {"Root":None, "Character":char}

		if len(char.children) == 0:
			gimbal = scene.addObject("Gimbal", char, 0)
			gimbal.setParent(char)
			gimbal.localPosition = self.createVector()
			gimbal.localOrientation = self.createMatrix()
			gimbal.worldScale = self.createVector(fill=1)*0.5

		self.findObjects(char)

		self.ANIMOBJ = self.objects.get("Rig", None)

		self.defaultStates()

		self.rayhit = None
		self.rayvec = None

		self.jump_state = "NONE"
		self.jump_timer = 0
		self.lastaction = [None,0]

		self.resetGroundRay()
		self.resetAcceleration()

		self.motion = {
			"Move": self.createVector(2),
			"Rotate": self.createVector(3),
			"Climb": 0,
			"Local": self.createVector(3),
			"World": self.createVector(3)
			}

		self.dict = char["DICT"]

		self.data = {"HEALTH":100, "ENERGY":100, "RECHARGE":0.02, "SPEED":self.SPEED,
			"JUMP":self.JUMP, "RUN":self.MOVERUN, "STRAFE":self.SIDESTEP}

		self.data["HUD"] = {"Text":"", "Color":(0,0,0,0.5), "Target":None, "Locked":None}

		self.data["POS_LEVEL"] = None
		self.data["PHYSICS"] = "DYNAMIC"
		self.data["CROUCH"] = 0
		self.data["DAMPING"] = [0, 0]
		self.data["LINVEL"] = [0,0,0]

		self.data["JP_STATE"] = self.jump_state
		self.data["JP_TIMER"] = self.jump_timer

		dict = self.defaultData()
		for key in dict:
			if key not in self.data:
				self.data[key] = dict[key]

		char["DEBUG1"] = ""
		char["DEBUG2"] = ""
		char["RAYTEXT"] = ""
		char.addDebugProperty("DEBUG1", True)
		char.addDebugProperty("DEBUG2", True)
		char.addDebugProperty("RAYTEXT", True)

		keymap.MOUSELOOK.center()

		self.doLoad()
		self.loadInventory(char)
		self.applyGravity()

		self.doPlayerAnim("RESET")

		self.ST_Startup()

		if self.dict["ID"] != None and self.dict.get("Vehicle", None) == None:
			self.switchPlayerActive(self.dict["ID"])
			self.PS_SetVisible(True)
			viewport.loadCamera()

	def defaultStates(self):
		self.active_pre = [self.PR_LastVelocity]
		self.active_state = self.ST_Walking
		self.active_post = [self.PS_Recharge, self.PS_SetVisible, self.PS_GroundTrack]

	def resetGroundRay(self):
		self.groundhit = None
		self.groundold = None
		self.groundobj = None
		self.groundchk = False
		self.groundvel = self.createVector()
		self.groundpos = [self.createVector(), self.createVector()]
		self.groundori = [self.createMatrix(), self.createMatrix()]

		self.gndraybias = self.GND_H

	def resetAcceleration(self, speed=(0,0,0)):
		self.accel_start = self.createVector(3)
		self.accel_move = self.createVector(vec=speed)
		self.accel_end = self.createVector(vec=speed)
		self.accel_timer = 0
		self.accel_stand = -1

	def doLoad(self):
		char = self.objects["Character"]

		base.PROFILE["PLRData"][char.name] = char["DICT"]

		if self.dict["Data"] == None:
			self.dict["Data"] =  self.data
			self.data["ACTIVE_STATE"] = self.active_state.__name__
		else:
			self.data = self.dict["Data"]
			self.active_state = getattr(self, self.data["ACTIVE_STATE"])

		self.jump_state = self.data["JP_STATE"]
		self.jump_timer = self.data["JP_TIMER"]

		newmap = str(base.CURRENT["Level"])+str(base.CURRENT["Scene"])

		if self.data["POS_LEVEL"] == newmap:
			char.worldPosition = self.data["POS"]
			char.worldOrientation = self.data["ORI"]
		else:
			self.data["POS_LEVEL"] = newmap
			self.data["POS"] = self.vecTuple(char.worldPosition)
			self.data["ORI"] = self.matTuple(char.worldOrientation)

		if "Add" in self.dict:
			base.LEVEL["SPAWN"].append(self.dict["Add"])
			del self.dict["Add"]

		if self not in logic.PLAYERLIST:
			logic.PLAYERLIST.append(self)

	def doUpdate(self):
		self.data["JP_STATE"] = self.jump_state
		self.data["JP_TIMER"] = self.jump_timer
		self.data["ACTIVE_STATE"] = self.active_state.__name__

		char = self.objects["Character"]

		self.data["POS"] = self.vecTuple(char.worldPosition)
		self.data["ORI"] = self.matTuple(char.worldOrientation)

		owner = self.objects["Root"]
		if owner == None:
			return

		self.data["LINVEL"] = self.vecTuple(owner.localLinearVelocity)
		self.data["DAMPING"] = [owner.linearDamping, owner.angularDamping]

	def addPhysicsBox(self):
		char = self.objects["Character"]

		owner = char.scene.addObject(self.PHYSICS, char, 0)
		owner.setDamping(self.data["DAMPING"][0], self.data["DAMPING"][1])
		owner["Class"] = self

		self.objects["Root"] = owner

		self.addCollisionCallBack()
		self.setPhysicsType()

		owner.localLinearVelocity = self.data["LINVEL"]

		return owner

	def removePhysicsBox(self):
		self.jump_state = "NONE"
		self.jump_timer = 0
		self.data["CROUCH"] = 0
		self.data["LINVEL"] = [0,0,0]

		if self.objects["Root"] != None:
			self.doCrouch(False)
			self.objects["Character"].removeParent()
			self.objects["Root"].endObject()
			self.objects["Root"] = None

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

	def assignCamera(self):
		viewport.setCamera(self)
		viewport.setParent(self.objects["Root"])
		self.setCameraState(None)

	def switchPlayerActive(self, ID=None):
		keymap.MOUSELOOK.center()

		self.doAnim(STOP=True)

		owner = self.addPhysicsBox()

		self.findObjects(owner)
		self.parentArmature(owner)
		self.assignCamera()

		self.doPlayerAnim("RESET")
		self.PS_SetVisible()

		HUD.SetLayout(self)
		if ID != None:
			self.dict["ID"] = ID
			base.WORLD["PLAYERS"][ID] = self.dict["Object"]

	def switchPlayerPassive(self):
		self.resetGroundRay()
		self.resetAcceleration()
		self.data["HUD"]["Target"] = None
		self.data["HUD"]["Text"] = ""

		self.removePhysicsBox()

		self.doPlayerAnim("RESET")

		ID = self.dict["ID"]
		self.dict["ID"] = None
		if ID in base.WORLD["PLAYERS"]:
			del base.WORLD["PLAYERS"][ID]
		return ID

	def enterVehicle(self, seat):
		self.dict["Vehicle"] = True
		self.dict["ID"] = self.switchPlayerPassive()

		self.parentArmature(seat, True)

	def exitVehicle(self, spawn):
		self.objects["Character"].removeParent() 

		self.switchPlayerActive(self.dict["ID"])

		self.dict["Vehicle"] = None

		owner = self.objects["Root"]
		owner.worldPosition = spawn

		self.alignToGravity(owner)

	def alignCamera(self, factor=1.0, axis=(0,1,0), up=None):
		vref = self.objects["Root"].getAxisVect(axis)
		if up == None:
			up = self.objects["Root"].getAxisVect((0,0,1))
		viewport.setDirection(vref, factor, up)

	def alignPlayer(self, factor=1.0, axis=None, up=None):
		if axis == None:
			axis = viewport.getDirection()
		self.objects["Root"].alignAxisToVect(axis, 1, factor)
		if up == None:
			self.alignToGravity()
		elif up != False:
			self.objects["Root"].alignAxisToVect(up, 2, 1.0)

	def getDropPoint(self):
		rotate = viewport.getObject("Rotate")
		drop = rotate.worldPosition+rotate.getAxisVect((0,self.INTERACT,0))

		if self.rayhit != None:
			if self.rayvec.length < (self.INTERACT+0.5):
				drop += (self.rayhit[2]*0.5)
			if self.rayvec.length < self.INTERACT:
				drop = self.rayhit[1]+(self.rayhit[2]*0.5)

		return drop

	def getInputs(self):
		FORWARD = keymap.BINDS["PLR_FORWARD"].axis() - keymap.BINDS["PLR_BACKWARD"].axis()
		STRAFE = keymap.BINDS["PLR_STRAFERIGHT"].axis() - keymap.BINDS["PLR_STRAFELEFT"].axis()
		MOVE = keymap.input.JoinAxis(STRAFE, FORWARD)

		TURN = keymap.BINDS["PLR_TURNLEFT"].axis() - keymap.BINDS["PLR_TURNRIGHT"].axis()
		LOOK = keymap.BINDS["PLR_LOOKUP"].axis() - keymap.BINDS["PLR_LOOKDOWN"].axis()
		ROTATE = keymap.input.JoinAxis(LOOK, 0, TURN)

		CLIMB = 0

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

		if keymap.BINDS["TOGGLECAM"].tap() == True:
			if self.data["CAMERA"]["State"] == "THIRD":
				self.setCameraState("FIRST")

			elif self.data["CAMERA"]["State"] == "FIRST":
				self.setCameraState("THIRD")

		if self.data["CAMERA"]["State"] == "THIRD":
			if keymap.BINDS["TOGGLESTRAFE"].tap() == True:
				self.data["STRAFE"] ^= True

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
				WPDROP += self.objects["Root"].getAxisVect((0,0,2))
			for slot in list(self.data["WEAPSLOT"].keys()):
				self.cls_dict[slot].dropItem(WPDROP)
				WPDROP += self.objects["Root"].getAxisVect((0,0,2))

	def setCameraState(self, state=None, load=False):
		if state == None:
			state = self.data["CAMERA"]["State"]
		else:
			self.data["CAMERA"]["State"] = state

		if state == "SHOULDER":
			pos = [self.CAM_SHSIDE, 0, self.EYE_H-self.GND_H-self.CAM_MIN]
		else:
			pos = [0, 0, self.EYE_H-self.GND_H]

		viewport.setState(state)
		viewport.setEyeHeight(eye=pos)

		#self.data["CAMERA"]["FOV"] = self.CAM_FOV
		self.data["CAMERA"]["State"] = state

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
			self.groundvel *= 0
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
				WALLNRM = owner.localOrientation.inverted()*WALLNRM
				WALLNRM[2] = 0
				WALLNRM.normalize()
				WALLNRM = owner.localOrientation*WALLNRM
			if WALLNRM.length > 0.01:
				angle = axis.angle(WALLNRM, 0)
				angle = round(self.toDeg(angle), 2)

		else:
			if simple != None:
				return None

		return angle, WALLNRM

	def checkGround(self, simple=False, ray=None):
		owner = self.objects["Root"]
		ground = None
		angle = 0
		move = self.motion["World"].copy()
		gndto = owner.getAxisVect((0,0,-1))+owner.worldPosition
		gndbias = 0
		tan = 0

		if ray == None:
			raylist = (gndto, None, self.gndraybias)
		else:
			raylist = ray

		rayOBJ, rayPNT, rayNRM = owner.rayCast(raylist[0], raylist[1], raylist[2]+0.3, "GROUND", 1, 1, 0)

		if rayOBJ == None or self.gravity.length < 0.1:
			self.gndraybias = self.GND_H

			if simple == True:
				return None

		else:
			ground = [rayOBJ, rayPNT, rayNRM]

			angle = owner.getAxisVect((0,0,1)).angle(rayNRM, 0)
			angle = round(self.toDeg(angle), 2)
			gndbias = (angle/90)*self.SLOPE_BIAS

			if self.jump_state not in ["NONE", "CROUCH"] and ray == None:
				dist = owner.worldPosition-rayPNT
				if dist.length > self.GND_H+gndbias:
					ground = None
				else:
					self.gndraybias = self.GND_H+gndbias

				#if angle > self.SLOPE:
				#	ground = None

			if simple == True:
				self.gndraybias = self.GND_H+gndbias
				return ground

		if ground != None:
			self.getGroundPoint(rayOBJ)

			if self.groundold != None:
				gnddiff = self.groundold[1]-rayPNT
				gnddiff = owner.worldOrientation.inverted()*gnddiff
				if abs(gnddiff[2]) < 0.4:
					self.gndraybias += gnddiff[2]

			self.groundhit = ground
			self.gndraybias += ((self.GND_H+gndbias)-self.gndraybias)*0.2

		return ground, angle

	def doInteract(self, rayfrom=None):
		scene = base.SC_SCN
		owner = self.objects["Root"]

		dist = 1000

		if self.data["CAMERA"]["State"] == "SHOULDER":
			if rayfrom == None:
				rayfrom = (0, 0, self.EYE_H-self.GND_H)
			rayfrom = self.getWorldSpace(owner, rayfrom)
		else:
			rayfrom = viewport.getObject("Rotate").worldPosition

		rayto = rayfrom+viewport.getRayVec()

		RAYHIT = owner.rayCast(rayto, rayfrom, dist, "", 1, 0, 0)

		RAYTARGPOS = [0.5, 0.5]

		self.rayhit = None
		self.rayvec = None

		if self.active_weapon != None:
			self.data["HUD"]["Color"] = (0,1,0,0.5)
			self.data["HUD"]["Text"] = self.active_weapon.NAME

		if RAYHIT[0] != None:
			self.rayhit = RAYHIT  #(RAYOBJ, RAYPNT, RAYNRM)
			self.rayvec = rayfrom-RAYHIT[1]

			screen = scene.active_camera.getScreenPosition(RAYHIT[1])
			RAYTARGPOS[0] = screen[0]
			RAYTARGPOS[1] = screen[1]

			if self.rayvec.length < self.INTERACT:
				RAYOBJ = RAYHIT[0]

				if "RAYCAST" in RAYOBJ:
					if self.active_weapon != None:
						self.data["HUD"]["Color"] = (1,0,0,1)
					else:
						self.data["HUD"]["Color"] = (0,1,0,1)
						RAYOBJ["RAYCAST"] = self

				elif self.rayvec.dot(RAYHIT[2]) < 0 and config.DO_STABILITY == True:
					self.data["HUD"]["Color"] = (0,0,1,1)
					self.data["HUD"]["Text"] = "Press "+keymap.BINDS["ACTIVATE"].input_name+" To Ghost Jump"
					if keymap.BINDS["ACTIVATE"].tap() == True:
						owner.worldPosition = RAYHIT[1]+(RAYHIT[2]*self.WALL_DIST)

				if RAYOBJ.get("RAYNAME", None) != None:
					self.data["HUD"]["Text"] = RAYOBJ["RAYNAME"]

		if self.groundhit != None:
			if "RAYFOOT" in self.groundhit[0]:
				self.groundhit[0]["RAYFOOT"] = self

		self.data["HUD"]["Target"] = RAYTARGPOS

	def doJump(self, height=None, move=0.5, align=False):
		owner = self.objects["Root"]

		self.jump_state = "JUMP"
		self.jump_timer = 0

		owner.setDamping(0, 0)

		if height == None:
			height = self.data["JUMP"]

		align = owner.localLinearVelocity.copy()*align
		align[2] = 0
		if align.length > 0.02 and move > 0:
			if self.data["STRAFE"] == False and self.data["CAMERA"]["State"] == "THIRD":
				self.alignPlayer(axis=owner.getAxisVect(align))

		owner.localLinearVelocity[0] *= move
		owner.localLinearVelocity[1] *= move

		owner.localLinearVelocity[2] = height

		self.doPlayerAnim("JUMP", 5)

	def doMovement(self, vec, mx=0):
		owner = self.objects["Root"]

		world = self.motion["World"].copy()
		local = self.motion["Local"].copy()

		if self.groundhit != None:
			rayNRM = self.groundhit[2]
		else:
			rayNRM = owner.getAxisVect((0,0,1))

		angle = owner.getAxisVect((0,0,1)).angle(rayNRM, 0)
		angle = round(self.toDeg(angle), 2)

		dot = 0
		if angle > 5 and local.length > 0.01:
			slvec = owner.worldOrientation.inverted()*rayNRM
			slvec[2] = 0

			slang = slvec.normalized().angle(local.normalized(), 0)
			slang = round(self.toDeg(slang), 2)

			if angle <= self.SLOPE:
				dot = abs(1-(slang/90))*self.SLOPE_SPEED

		slope = 1-(dot*(angle/90))
		self.objects["Character"]["DEBUG2"] = slope
		vref = viewport.getDirection(vec)
		mref = (vref*mx*slope)

		if self.ACCEL < 1:
			move = mref.copy()
		else:
			check = self.accel_end-mref
			if check.length > 0.001:
				self.accel_start = self.accel_move.copy()
				self.accel_end = mref.copy()
				self.accel_timer = 0
				if self.accel_stand == -1 and self.accel_start.length < 0.001:
					self.accel_stand = 0
				elif self.accel_start.normalized().dot(self.accel_end.normalized()) < 0:
					self.accel_stand = 0

			rate = (1/self.ACCEL)
			if self.accel_stand == -1:
				rate = (1/self.ACCEL_FAST)
			if self.accel_end.length < 0.001:
				rate = (1/self.ACCEL_STOP)

			offset = mref-self.accel_start
			self.accel_move += offset*rate
			check = mref-self.accel_move

			greater = offset.normalized().dot(check.normalized())

			if greater < 0 or check.length < 0.001:
				self.accel_move = mref.copy()

			if self.accel_timer < self.ACCEL:
				self.accel_timer += 1
			else:
				self.accel_timer = self.ACCEL

			if self.accel_stand >= 0:
				self.accel_stand += 1
			if self.accel_stand >= self.ACCEL:
				self.accel_stand = -1

			move = self.accel_move.copy()

		if angle > 5 and angle <= self.SLOPE and world.length > 0.001:
			tango = rayNRM.angle(world.normalized(), 0)
			tango = round(self.toDeg(tango), 2)

			tan = self.getSlopeOffset(tango-90, world.length/60)
			tangle = owner.getAxisVect((0,0,1))*tan
			move += tangle

		owner.worldLinearVelocity = move*60

	def doMoveAlign(self, axis=None, up=None, margin=0.002):
		owner = self.objects["Root"]

		if axis != None:
			align = self.createVector(vec=axis)
		elif self.data["STRAFE"] == True or self.data["CAMERA"]["State"] != "THIRD":
			align = viewport.getDirection((0,1,0))
		else:
			align = owner.worldLinearVelocity*(1/60)

		align = owner.worldOrientation.inverted()*align
		align[2] = 0
		align = owner.worldOrientation*align

		if align.length >= margin:
			align.normalize()
			dref = owner.getAxisVect((0,1,0))
			dot = 1-((dref.dot(align)*0.5)+0.5)
			dot = 0.2+((dot**2)*0.5)

			self.alignPlayer(dot, align, up)

		elif up == None:
			self.alignToGravity()
		elif up != False:
			owner.alignAxisToVect(up, 2, 1.0)

	def doPlayerOnGround(self):
		scene = base.SC_SCN
		owner = self.objects["Root"]
		char = self.objects["Character"]

		move = self.motion["Move"].normalized()

		if self.data["RUN"] == False or self.motion["Move"].length <= 0.7 or self.data["SPEED"] <= 0:
			mx = 0.035
		else:
			mx = self.data["SPEED"]

		self.doMovement((move[0], move[1], 0), mx)
		self.doMoveAlign(up=False)
		self.doPlayerAnim("MOVE", blend=10)

		## Jump/Crouch ##
		if keymap.BINDS["PLR_DUCK"].active() == True:
			self.doCrouch(True)

		elif keymap.BINDS["PLR_JUMP"].tap() == True:
			if self.jump_timer == 1:
				self.jump_timer = 2
		elif keymap.BINDS["PLR_JUMP"].active() == True:
			if self.jump_timer >= 2:
				self.jump_timer += 1
			if self.jump_timer >= 7:
				self.doJump(move=0.8, align=True)
		elif keymap.BINDS["PLR_JUMP"].released() == True:
			if self.jump_timer >= 1 and self.jump_timer < 7:
				self.doJump(height=self.JUMP/1.5, move=1.0, align=False)
		else:
			self.jump_timer = 1

	def doPlayerAnim(self, action="MOVE", blend=10):
		if self.ANIMOBJ == None:
			return

		if action == "JUMP":
			self.doAnim(NAME="Jumping", FRAME=(0,20), PRIORITY=2, MODE="PLAY", BLEND=10)
			self.lastaction = [action, 0]
			return

		if action == "FALLING":
			self.doAnim(NAME="Jumping", FRAME=(40,40), PRIORITY=3, MODE="LOOP", BLEND=blend)
			self.lastaction = [action, 0]
			return

		if action in ["IDLE", "RESET"]:
			invck = 0
			for slot in self.cls_dict:
				if slot in ["Hip_L", "Hip_R"]:
					invck = -5

			if action == "RESET":
				self.doAnim(NAME="Jumping", FRAME=(0+invck,0+invck))
			else:
				self.doAnim(NAME="Jumping", FRAME=(0+invck,0+invck), PRIORITY=3, MODE="LOOP", BLEND=blend)
			self.lastaction = [action, 0]
			return

		linLV = self.motion["Local"]

		if action == "CROUCH":
			if linLV.length > 0.1:
				self.doAnim(NAME="Crouching", FRAME=(0,80), PRIORITY=3, MODE="LOOP", BLEND=blend)
			else:
				self.doAnim(NAME="Crouching", FRAME=(0,0), PRIORITY=3, MODE="LOOP", BLEND=blend)
			self.lastaction = [action, 0]
			return

		action = "IDLE"
		walk = False
		stair = ""
		setframe = 0

		if linLV.length > 0.1:
			if self.ACCEL > 10 and self.accel_stand >= 0:
				blend = self.ACCEL

			if linLV.length < (0.05*60):
				walk = True

			action = "FORWARD"

			if linLV[1] < 0:
				action = "BACKWARD"
			if linLV[0] > 0.5 and abs(linLV[1]) < 0.5:
				action = "STRAFE_R"
			if linLV[0] < -0.5 and abs(linLV[1]) < 0.5:
				action = "STRAFE_L"

			angle = self.objects["Character"].getAxisVect((0,0,1)).angle(self.groundhit[2], 0)
			angle = round(self.toDeg(angle), 2)

			if angle > 20 and angle <= self.SLOPE:
				stair = ".Stairs"

		## ANIMATIONS ##
		if action == "FORWARD":
			if walk == True:
				self.doAnim(NAME="Walking", FRAME=(0,59), PRIORITY=3, MODE="LOOP", BLEND=blend)
				setframe = 59
			else:
				self.doAnim(NAME="Running"+stair, FRAME=(0,39), PRIORITY=3, MODE="LOOP", BLEND=blend)
				setframe = 39

		elif action == "BACKWARD":
			#if walk == True:
			self.doAnim(NAME="Walking", FRAME=(59,0), PRIORITY=3, MODE="LOOP", BLEND=blend)
			setframe = 59
			#else:
			#	self.doAnim(NAME="Running"+stair, FRAME=(39,0), PRIORITY=3, MODE="LOOP", BLEND=blend)
			#	setframe = 39

		else:
			self.lastaction = ["IDLE", 0]
			self.doPlayerAnim("IDLE")
			return

		if self.lastaction[0] != action:
			self.lastaction[0] = action
			self.doAnim(SET=self.lastaction[1]*setframe)

		self.lastaction[1] = self.doAnim(CHECK="FRAME")/setframe

	def doCrouch(self, state):
		self.jump_timer = 0
		if state == True or self.data["CROUCH"] != 0:
			self.jump_state = "CROUCH"
			self.objects["Root"].localScale[2] = self.CROUCH_SCALE
			self.objects["Character"].localScale[2] = 1/self.CROUCH_SCALE
			self.active_state = self.ST_Crouch
		elif state == False:
			self.jump_state = "NONE"
			self.objects["Root"].localScale[2] = 1
			self.objects["Character"].localScale[2] = 1
			self.objects["Character"].localPosition = (0,0,0)
			self.active_state = self.ST_Walking

	## INIT STATE ##
	def ST_Startup(self):
		if self.jump_state == "FLYING" and self.objects["Root"] != None:
			self.ST_Advanced_Set()

	## PRE ##
	def PR_LastVelocity(self):
		owner = self.objects["Root"]

		gndvel = self.groundvel.copy()

		if owner != None:
			linWV = owner.worldLinearVelocity-gndvel
			linLV = owner.worldOrientation.inverted()*linWV
			linLV[2] = 0
			linWV = owner.worldOrientation*linLV
		else:
			linWV = self.createVector()
			linLV = self.createVector()

		self.motion["Local"] = linLV
		self.motion["World"] = linWV

	## POST ##
	def PS_Recharge(self):
		if self.data["HEALTH"] < 0:
			self.data["HEALTH"] = -1
		if self.data["ENERGY"] < 100:
			self.data["ENERGY"] += self.data["RECHARGE"]
			if self.data["ENERGY"] > 100:
				self.data["ENERGY"] = 100
		if self.data["HEALTH"] > 200:
			self.data["HEALTH"] = 200
		if self.data["ENERGY"] > 200:
			self.data["ENERGY"] = 200

	def PS_GroundTrack(self):
		owner = self.objects["Root"]
		self.groundchk = False

		if self.groundhit == None or self.jump_state not in ["NONE", "CROUCH", "JUMP"]:
			drag = self.AIR_DRAG
			dragX = owner.localLinearVelocity[0]*drag[0] #0.67
			dragY = owner.localLinearVelocity[1]*drag[1] #0.67
			dragZ = owner.localLinearVelocity[2]*drag[2] #0.33
			owner.applyForce((-dragX, -dragY, -dragZ), True)
			self.groundvel *= 0
			self.groundhit = None
			self.groundold = None
			self.groundobj = None
			return

		rayOBJ = self.groundobj
		wp = owner.worldPosition

		locOLD = wp - self.groundpos[1]
		posOLD = self.groundori[1].inverted()*locOLD

		locNEW = wp - self.groundpos[0]
		posNEW = self.groundori[0].inverted()*locNEW

		local = posOLD - posNEW
		offset = self.groundori[0]*local

		if self.data["PHYSICS"] == "NONE":
			owner.applyMovement(offset, False)
		else:
			owner.worldLinearVelocity += offset*60

		yvec = owner.getAxisVect((0,1,0))
		rotOLD = self.groundori[1].inverted()*yvec
		rotOLD = self.groundori[0]*rotOLD
		euler = yvec.rotation_difference(rotOLD).to_euler()

		owner.applyRotation((0,0,euler[2]), True)

		owner.applyForce(-self.gravity, False)

		self.groundvel = offset.copy()*60
		self.groundold = self.groundhit.copy()
		self.groundold[1] += owner.worldLinearVelocity/60
		self.groundhit = None

	def PS_SetVisible(self, state=None):
		owner = self.objects["Root"]
		char = self.objects["Character"]
		if state != None:
			char.setVisible(state, True)
		elif self.data["CAMERA"]["State"] == "FIRST" and viewport.getController() == self:
			char.setVisible(False, True)
		else:
			char.setVisible(True, True)
		if "SKT" in self.objects:
			for key in self.HAND:
				hand = self.HAND[key]
				skt = self.objects["SKT"].get(hand, None)
				if skt != None:
					skt.setVisible(True, True)

	## WALKING STATE ##
	def ST_Crouch(self):
		scene = base.SC_SCN
		owner = self.objects["Root"]
		char = self.objects["Character"]

		fac = self.data["CROUCH"]*0.1
		if self.data["CROUCH"] < 0:
			fac = (self.data["CROUCH"]+10)*-0.1

		## EYE HEIGHT ##
		owner.localScale[2] = self.CROUCH_SCALE
		char.localScale[2] = 1/self.CROUCH_SCALE
		char.localPosition[2] = fac*(1/self.CROUCH_SCALE)*self.CROUCH_H

		cr_fac = self.GND_H-(fac*self.CROUCH_H)

		eyevec = [0, 0, (self.EYE_H-self.GND_H)]

		if self.data["CAMERA"]["State"] == "SHOULDER":
			eyevec[0] = self.CAM_SHSIDE
			eyevec[2] -= self.CAM_MIN

		eyevec[2] *= cr_fac

		viewport.setEyeHeight(eye=eyevec, set=True)

		## MOVEMENT ##
		ground, angle = self.checkGround()

		owner.setDamping(0, 0)

		if ground != None:
			gpos = ground[1]+(owner.getAxisVect((0,0,1))*(self.gndraybias*cr_fac))
			owner.worldPosition = gpos
			owner.worldLinearVelocity = (0,0,0)

			if ground[0].getPhysicsId() != 0:
				impulse = self.gravity*owner.mass*0.1
				ground[0].applyImpulse(ground[1], impulse, False)

			axis = owner.getAxisVect((0,0,2))
			point = ground[1]+axis
			dist = point-owner.worldPosition

			chkwall = True
			if self.data["CROUCH"] == -20:
				if keymap.BINDS["PLR_DUCK"].released() == True:
					chkwall = False
			elif self.data["CROUCH"] < -5:
				chkwall = False

			if self.checkWall(axis=axis.normalized(), simple=dist.length) != None:
				chkwall = True

		else:
			chkwall = False

		mx = 0
		move = self.motion["Move"].normalized()
		if self.motion["Move"].length > 0.01:
			mx = 0.02

		self.doMovement((move[0], move[1], 0), mx)
		self.doMoveAlign()

		self.doInteract(rayfrom=[0,0,(self.EYE_H-self.GND_H)*cr_fac])
		self.checkStability()
		self.weaponManager()

		if chkwall == False and self.data["CROUCH"] < -5:
			self.doPlayerAnim("IDLE", blend=10)

			if self.data["CROUCH"] == -10:
				self.data["CROUCH"] = 0
				self.doCrouch(False)
			else:
				self.data["CROUCH"] += 1

		else:
			self.doPlayerAnim("CROUCH", blend=10)

			if self.data["CROUCH"] == 10:
				self.data["CROUCH"] = -20
			elif self.data["CROUCH"] >= 0:
				self.data["CROUCH"] += 1

		self.objects["Character"]["DEBUG1"] = self.data["CROUCH"]

	def ST_Walking(self):
		scene = base.SC_SCN
		owner = self.objects["Root"]
		char = self.objects["Character"]

		move = self.motion["Move"].normalized()

		ground, angle = self.checkGround()

		owner.setDamping(0, 0)

		if ground != None:
			gpos = ground[1]+(owner.getAxisVect((0,0,1))*self.gndraybias)

			if self.jump_state in ["FALLING", "A_JUMP", "B_JUMP", "NO_AIR"] and owner.localLinearVelocity[2] < 0.1:
				self.jump_timer = 0
				self.jump_state = "NONE"
				if ground[0].getPhysicsId() != 0:
					impulse = (owner.worldLinearVelocity+self.gravity)*owner.mass*0.1
					ground[0].applyImpulse(ground[1], impulse, False)
				Z = owner.localLinearVelocity[2]
				if Z < -8:
					self.data["HEALTH"] += (Z+8)*self.GRAV_DAMAGE
				self.doAnim(STOP=True)
				self.resetAcceleration(owner.worldLinearVelocity*(1/60))
				self.accel_timer = self.ACCEL

			if self.jump_state == "NONE":
				owner.worldPosition = gpos
				owner.worldLinearVelocity = (0,0,0)

				self.doPlayerOnGround()

				if ground[0].getPhysicsId() != 0:
					impulse = self.gravity*owner.mass*0.1
					ground[0].applyImpulse(ground[1], impulse, False)

			elif self.jump_state in ["JUMP", "JP_WAIT"]:
				self.jump_state = "JP_WAIT"
				self.jump_timer += 1

				if self.jump_timer > 10:
					self.doAnim(STOP=True)
					self.jump_timer = 0
					self.jump_state = "NONE"
			else:
				gdif = owner.worldOrientation.inverted()*(owner.worldPosition-gpos)
				if gdif[2] < 0:
					owner.worldPosition = gpos
					owner.localLinearVelocity[2] = 0

				if keymap.BINDS["PLR_JUMP"].active() == True:
					self.jump_state = "B_JUMP"
				else:
					self.doAnim(STOP=True)
					self.jump_state = "FALLING"

		else:
			self.doPlayerAnim("FALLING")

			if self.jump_state in ["FALLING", "A_JUMP", "B_JUMP", "NO_AIR"]:
				if self.data["CAMERA"]["State"] != "THIRD":
					self.doMoveAlign(up=False)

				if self.gravity.length < 0.1 and self.rayvec != None:
					if self.rayvec.length < self.INTERACT:
						self.data["HUD"]["Color"] = (0, 1, 0, 0.5)
						self.data["HUD"]["Text"] = "Press "+keymap.BINDS["PLR_JUMP"].input_name+" To Wall Shove"
						if keymap.BINDS["PLR_JUMP"].tap() == True:
							owner.worldLinearVelocity = self.rayvec.normalized()*6

					vref = (self.motion["Move"][0], self.motion["Move"][1], self.motion["Climb"])
					vref = viewport.getDirection(vref)
					vref.normalize()
					owner.applyForce(vref*1, False)

				if self.jump_state != "NO_AIR" and self.gravity.length >= 0.1:
					vref = viewport.getDirection((move[0], move[1], 0))
					owner.applyForce(vref*5, False)

			if self.jump_state in ["NONE", "JUMP"]:
				if self.jump_state == "NONE" and self.gravity.length >= 0.1:
					if keymap.BINDS["PLR_JUMP"].active() == True and self.jump_timer >= 1:
						self.doJump(move=0.8, align=True)
					elif keymap.BINDS["PLR_DUCK"].active() != True:
						self.doJump(height=1, move=0.5)
				self.jump_state = "A_JUMP"

			if keymap.BINDS["PLR_JUMP"].active() == True:
				if self.jump_state == "FALLING":
					self.jump_state = "B_JUMP"
			else:
				self.jump_state = "FALLING"

			self.jump_timer += 1

		self.alignToGravity()

		self.objects["Character"]["DEBUG1"] = self.data["CROUCH"]
		#self.objects["Character"]["DEBUG2"] = str(self.jump_state)

		self.doInteract()
		self.checkStability()
		self.weaponManager()

		if keymap.BINDS["TOGGLEMODE"].tap() == True:
			self.ST_Advanced_Set()

	def ST_Walking_Set(self):
		self.doAnim(STOP=True)
		self.resetAcceleration()
		self.active_state = self.ST_Walking

	## FLY STATE ##
	def ST_FlySimple(self):
		scene = base.SC_SCN
		owner = self.objects["Root"]

		mx = 10
		move = self.motion["Move"]
		climb = self.motion["Climb"]

		owner.setDamping(0.5, 0.5)
		owner.applyForce(-self.gravity, False)
		owner.applyForce((move[0]*mx, move[1]*mx, climb*mx), True)

		self.doMoveAlign()

		self.doPlayerAnim("FALLING")

		if keymap.BINDS["TOGGLEMODE"].tap() == True:
			self.jump_state = "FALLING"
			self.ST_Walking_Set()

	def ST_Advanced_Set(self):
		self.jump_state = "FLYING"
		self.data["HUD"]["Target"] = None
		self.active_state = self.ST_FlySimple

	def ST_Freeze(self):
		pass

	## RUN ##
	def RUN(self):
		if self.objects["Root"] == None:
			self.ST_Freeze()
			self.PS_Attachments()
			return
		self.runPre()
		self.getInputs()
		self.runStates()
		self.runPost()



