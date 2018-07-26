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

## VEHICLE CORE ##


from bge import logic, constraints

import PYTHON.base as base
import PYTHON.keymap as keymap
import PYTHON.HUD as HUD


class CoreVehicle(base.CoreAdvanced):

	NAME = "Vehicle"
	PORTAL = True
	SPAWN = (-1, 0, 0)
	PLAYERACTION = "SeatLow"

	CAMFIRST = {"POS":(0,0,0)}
	CAMTHIRD = {"DIST":10, "ZRATIO":0.1, "MIN":1, "SLOW":10, "RANGE":(4, 16)}

	WHEELOBJECT = {"MESH":"Wheel.Small", "RADIUS":0.2, "COLOR":(1,1,1,1)}
	WHEELSETUP = {"FRONT":1, "REAR":-1, "WIDTH":1, "HEIGHT":0.25, "LENGTH":0.25}
	WHEELCONFIG = {"ROLL":0.1, "SPRING":50, "DAMPING":10, "FRICTION":5}

	def __init__(self):
		owner = logic.getCurrentController().owner

		owner["Class"] = self

		owner["RAYCAST"] = owner.get("RAYCAST", None)
		owner["RAYNAME"] = self.NAME

		spawn = base.SC_SCN.addObject("Vehicle.Spawn", owner, 0)
		spawn.setParent(owner)
		spawn.localPosition = self.SPAWN

		self.objects = {"Root":owner, "Wheels":[], "Spawn":spawn}

		self.active_pre = []
		self.active_state = self.ST_Idle
		self.active_post = []

		self.driving_player = None

		self.vehicle_constraint = None
		self.cid = 999

		self.data = self.defaultData()
		self.data["HEALTH"] = 100
		self.data["ENERGY"] = 100
		self.data["CAMERA"] = {"State":3, "Orbit":False, "Dist":self.CAMTHIRD["DIST"], "Zoom":self.CAMTHIRD["DIST"]}
		self.data["HUD"] = {"Text":"", "Color":(0,0,0,0.5), "Target":None}
		self.data["PORTAL"] = False
		self.data["LINVEL"] = (0,0,0)

		self.linV = owner.getLinearVelocity(True)
		self.motion = {"Force": self.createVector(), "Torque": self.createVector()}

		self.addCollisionCallBack()

		self.createCamera()
		self.checkGhost(owner)
		self.findObjects(owner)
		self.doLoad()
		self.createVehicle()
		self.ST_Startup()
		self.doPortal()

		self.loadInventory(owner)
		self.doCameraCollision()

	def doPortal(self):
		owner = self.objects["Root"]

		if self.data["PORTAL"] == True:
			door = base.DATA["Portal"]["Door"]
			zone = base.DATA["Portal"]["Zone"]
			portal = owner.scene.objects.get(str(door), None)

			if portal != None:
				pos = portal.worldPosition
				ori = portal.worldOrientation

				owner.worldPosition = pos
				owner.worldOrientation = ori

			if zone != None:
				pos = self.createVector(vec=zone[0])
				pos = portal.worldPosition+(portal.worldOrientation*pos)

				dr = portal.worldOrientation.to_euler()
				ori = (zone[1][0]+dr[0], zone[1][1]+dr[1], zone[1][2]+dr[2])
				ori = self.createMatrix(rot=ori, deg=False)

				owner.worldPosition = pos
				owner.worldOrientation = ori

			owner.localLinearVelocity = self.data["LINVEL"]

			base.DATA["Portal"]["Door"] = None
			base.DATA["Portal"]["Zone"] = None
			base.DATA["Portal"]["Vehicle"] = None
			self.ST_Active_Set()

	def doUpdate(self, world=True):
		owner = self.objects["Root"]

		self.data["LINVEL"] = self.vecTuple(owner.localLinearVelocity)

		if self.data["PORTAL"] == True:
			base.LEVEL["PLAYER"]["POS"] = self.vecTuple(owner.worldPosition)
			base.LEVEL["PLAYER"]["ORI"] = self.matTuple(owner.worldOrientation)
			base.DATA["Portal"]["Vehicle"] = {"Object":owner.name, "Data":self.data}

			if world == True:
				for cls in logic.UPDATELIST:
					if cls != self:
						cls.doUpdate()

		else:
			self.saveWorldPos()

			if self.UPDATE == True and owner["DICT"] not in base.LEVEL["DROP"]:
				base.LEVEL["DROP"].append(owner["DICT"])

	def createCamera(self):
		owner = self.objects["Root"]
		scene = owner.scene

		third = scene.addObject("Vehicle.CamThird.Loc", owner, 0)
		third.setParent(owner)
		third.localPosition = (0,0,0)

		for child in third.childrenRecursive:
			if child.name.split(".")[2] == "Cam":
				child.timeOffset = 0

		first = scene.addObject("Vehicle.CamFirst.Loc", owner, 0)
		first.setParent(owner)
		first.localPosition = self.CAMFIRST["POS"]

	def getConstraint(self):
		owner = self.objects["Root"]

		if hasattr(constraints, "createVehicle") == True:
			vehicle = constraints.createVehicle(owner.getPhysicsId())
		else:
			vehicle = constraints.createConstraint(owner.getPhysicsId(), 0, constraints.VEHICLE_CONSTRAINT)

		self.cid = vehicle.getConstraintId()
		vehicle = constraints.getVehicleConstraint(self.cid)

		return vehicle

	def createVehicle(self):
		self.vehicle_constraint = self.getConstraint()

		setup = self.WHEELSETUP

		self.addWheel((setup["WIDTH"], setup["FRONT"], setup["HEIGHT"]))
		self.addWheel((-setup["WIDTH"], setup["FRONT"], setup["HEIGHT"]))
		self.addWheel((setup["WIDTH"], setup["REAR"], setup["HEIGHT"]))
		self.addWheel((-setup["WIDTH"], setup["REAR"], setup["HEIGHT"]))

	def removeVehicle(self):
		constraints.removeConstraint(self.cid)

		for wheel in self.objects["Wheels"]:
			wheel.endObject()

		self.vehicle_constraint = None
		self.objects["Wheels"] = []
		self.cid = 999

	def addWheel(self, pos):
		dict = self.WHEELOBJECT
		setup = self.WHEELSETUP
		config = self.WHEELCONFIG

		obj = base.SC_SCN.addObject(dict["MESH"], self.objects["Root"], 0)

		if pos[0] < 0:
			obj.localScale = (-1,1,1)

		self.vehicle_constraint.addWheel(obj, (pos[0], pos[1], -pos[2]), (0,0,-1), (-1,0,0), setup["LENGTH"], dict["RADIUS"], True)

		id = len(self.objects["Wheels"])

		self.vehicle_constraint.setRollInfluence(config["ROLL"], id)
		self.vehicle_constraint.setSuspensionStiffness(config["SPRING"], id)
		self.vehicle_constraint.setSuspensionDamping(config["DAMPING"], id)
		self.vehicle_constraint.setTyreFriction(config["FRICTION"], id)
		self.vehicle_constraint.setSuspensionCompression(0.0, id)

		obj.color = dict.get("COLOR", obj.color)

		self.objects["Wheels"].append(obj)
		return obj

	def hideObject(self):
		self.objects["Root"].setVisible(False, True)
		for wheel in self.objects["Wheels"]:
			wheel.setVisible(False, True)

	def setCamera(self, CAM=0):
		self.objects["CamThird"]["Cam"].timeOffset = self.CAMTHIRD["SLOW"]
		self.data["CAMERA"]["Dist"] = self.data["CAMERA"]["Zoom"]

		if CAM == 0:
			CAM = self.data["CAMERA"]["State"]

		if CAM == 3:
			base.SC_SCN.active_camera = self.objects["CamThird"]["Cam"]
			self.objects["Seat"]["1"].setVisible(True, True)
			self.data["CAMERA"]["State"] = 3

		elif CAM == 1:
			base.SC_SCN.active_camera = self.objects["CamFirst"]["Cam"]
			self.objects["Seat"]["1"].setVisible(False, True)
			self.data["CAMERA"]["State"] = 1

	def doCameraState(self):
		camdata = self.data["CAMERA"]

		if self.data["CAMERA"]["State"] == 1:
			if keymap.BINDS["TOGGLECAM"].tap() == True:
				self.setCamera(3)

		elif self.data["CAMERA"]["State"] == 3:
			if keymap.BINDS["TOGGLECAM"].tap() == True:
				self.setCamera(1)

		## Set Camera Zoom ##
		camdata["Dist"] += (camdata["Zoom"]-camdata["Dist"])*0.1

		if keymap.BINDS["ZOOM_IN"].tap() == True and camdata["Zoom"] > self.CAMTHIRD["RANGE"][0]:
			camdata["Zoom"] -= 1

		elif keymap.BINDS["ZOOM_OUT"].tap() == True and camdata["Zoom"] < self.CAMTHIRD["RANGE"][1]:
			camdata["Zoom"] += 1

		## Toggle Orbit ##
		if self.data["CAMERA"]["Orbit"] == False:
			keymap.MOUSELOOK.center()

			if keymap.BINDS["CAM_ORBIT"].tap() == True:
				self.data["CAMERA"]["Orbit"] = True

		elif self.data["CAMERA"]["Orbit"] == True:
			X, Y = keymap.MOUSELOOK.axis()

			self.objects["CamFirst"]["Loc"].applyRotation((0,0,X), True)
			self.objects["CamFirst"]["Rot"].applyRotation((Y,0,0), True)

			if keymap.BINDS["CAM_ORBIT"].tap() == True:
				self.data["CAMERA"]["Orbit"] = False
				self.objects["CamFirst"]["Loc"].localOrientation = self.createMatrix()
				self.objects["CamFirst"]["Rot"].localOrientation = self.createMatrix()

			self.objects["CamThird"]["Loc"].localOrientation = self.objects["CamFirst"]["Loc"].localOrientation.copy()
			self.objects["CamThird"]["Rot"].localOrientation = self.objects["CamFirst"]["Rot"].localOrientation.copy()

	def doCameraCollision(self):
		camdata = self.data["CAMERA"]
		setup = self.CAMTHIRD
		objects = self.objects["CamThird"]

		margin = 1
		height = setup["ZRATIO"]
		dist = camdata["Dist"]

		camera = objects["Cam"]
		rayfrom = objects["Rot"]
		rayto = objects["Ray"]

		rayto.localPosition = (0, -dist, dist*height)

		hyp = (dist+margin)**2 + ((dist+margin)*height)**2

		rayOBJ, rayPNT, rayNRM = self.objects["Root"].rayCast(rayto, rayfrom, hyp**0.5, "GROUND", 0, 0, 0)

		camLX = 0.0
		camLY = -dist
		camLZ = dist*height

		if rayOBJ:
			rayto.worldPosition = rayPNT

			margin = margin*(abs(rayto.localPosition[1])/(dist+margin))

			camLX = 0.0
			camLY = rayto.localPosition[1]+margin
			camLZ = rayto.localPosition[2]-(margin*height)

		if camLZ < setup["MIN"]:
			camLZ = setup["MIN"]

		camera.localPosition[0] = camLX
		camera.localPosition[1] = camLY
		camera.localPosition[2] = camLZ

	def getInputs(self):
		self.linV = self.objects["Root"].getLinearVelocity(True)

		STRAFE = keymap.BINDS["VEH_STRAFERIGHT"].axis() - keymap.BINDS["VEH_STRAFELEFT"].axis()
		POWER = keymap.BINDS["VEH_THROTTLEUP"].axis() - keymap.BINDS["VEH_THROTTLEDOWN"].axis()
		CLIMB = keymap.BINDS["VEH_ASCEND"].axis() - keymap.BINDS["VEH_DESCEND"].axis()

		if keymap.BINDS["VEH_STRAFERIGHT"].active() == True:
			STRAFE = 1

		if keymap.BINDS["VEH_STRAFELEFT"].active() == True:
			STRAFE = -1

		if keymap.BINDS["VEH_THROTTLEUP"].active() == True:
			POWER = 1

		if keymap.BINDS["VEH_THROTTLEDOWN"].active() == True:
			POWER = -1

		if keymap.BINDS["VEH_ASCEND"].active() == True:
			CLIMB = 1

		if keymap.BINDS["VEH_DESCEND"].active() == True:
			CLIMB = -1

		self.motion["Force"][0] = STRAFE
		self.motion["Force"][1] = POWER
		self.motion["Force"][2] = CLIMB

		PITCH = keymap.BINDS["VEH_PITCHUP"].axis() - keymap.BINDS["VEH_PITCHDOWN"].axis()
		BANK = keymap.BINDS["VEH_BANKRIGHT"].axis() - keymap.BINDS["VEH_BANKLEFT"].axis()
		YAW = keymap.BINDS["VEH_YAWLEFT"].axis() - keymap.BINDS["VEH_YAWRIGHT"].axis()

		if keymap.BINDS["VEH_PITCHUP"].active() == True:
			PITCH = 1

		if keymap.BINDS["VEH_PITCHDOWN"].active() == True:
			PITCH = -1

		if keymap.BINDS["VEH_BANKRIGHT"].active() == True:
			BANK = 1

		if keymap.BINDS["VEH_BANKLEFT"].active() == True:
			BANK = -1

		if keymap.BINDS["VEH_YAWLEFT"].active() == True:
			YAW = 1

		if keymap.BINDS["VEH_YAWRIGHT"].active() == True:
			YAW = -1

		self.motion["Torque"][0] = PITCH
		self.motion["Torque"][1] = BANK
		self.motion["Torque"][2] = YAW

		if keymap.SYSTEM["SCREENSHOT"].tap() == True:
			self.doScreenshot()

		#if keymap.SYSTEM["LAUNCHER"].tap() == True:
		#	self.doUpdate()
		#	PATH = base.DATA["GAMEPATH"]
		#	logic.startGame(PATH+"Launcher.blend")

	def checkClicked(self, OBJ=None):
		if OBJ == None:
			OBJ = self.objects["Root"]

		if OBJ["RAYCAST"] != None:
			if keymap.BINDS["ENTERVEH"].tap() == True or keymap.BINDS["ACTIVATE"].tap() == True:
				if OBJ["RAYCAST"].data.get("WPDATA", None) != None:
					if OBJ["RAYCAST"].active_weapon != None:
						return False
				return True
		return False

	## IDLE STATE ##
	def ST_Idle(self):
		owner = self.objects["Root"]

		if self.checkClicked() == True:
			self.ST_Active_Set()

	def ST_Idle_Set(self):
		owner = self.objects["Root"]
		spawn = self.objects["Spawn"]
		dist = owner.getDistanceTo(spawn)

		rayOBJ = owner.rayCastTo(spawn, dist+0.5, "GROUND")
		if rayOBJ != None:
			return

		self.driving_player.exitVehicle(spawn)
		self.driving_player = None
		self.data["PORTAL"] = False
		self.active_state = self.ST_Idle

	## ACTIVE STATE ##
	def ST_Active(self):
		self.doCameraState()
		self.doCameraCollision()
		self.getInputs()

		owner = self.objects["Root"]

		if keymap.BINDS["ENTERVEH"].tap() == True:
			self.ST_Idle_Set()

	def ST_Active_Set(self):
		self.setCamera()
		self.driving_player = self.objects["Root"]["RAYCAST"]
		self.driving_player.enterVehicle(self.objects["Seat"]["1"], self.PLAYERACTION)
		logic.HUDCLASS.setControl(self)
		self.data["PORTAL"] = True
		self.active_state = self.ST_Active

	## RUN ##
	def alignSpawner(self):
		vref = self.objects["Root"].getAxisVect((0,1,0))
		self.objects["Spawn"].alignAxisToVect(vref, 1, 1.0)
		self.objects["Spawn"].alignAxisToVect((0,0,1), 2, 1.0)

	def RUN(self):
		self.runPre()
		self.alignSpawner()
		self.runStates()
		self.runPost()
		self.clearRayProps()
		self.checkStability(True)


