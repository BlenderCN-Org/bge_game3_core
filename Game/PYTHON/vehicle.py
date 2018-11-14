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
		self.data["CAMERA"] = {"State":3, "Orbit":None, "Dist":self.CAMTHIRD["DIST"], "Zoom":self.CAMTHIRD["DIST"]}
		self.data["HUD"] = {"Text":"", "Color":(0,0,0,0.5), "Target":None}
		self.data["PORTAL"] = False
		self.data["LINVEL"] = (0,0,0)
		self.data["ANGVEL"] = (0,0,0)

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

			owner.setLinearVelocity(self.data["LINVEL"], True)
			owner.setAngularVelocity(self.data["ANGVEL"], True)

			base.DATA["Portal"]["Door"] = None
			base.DATA["Portal"]["Zone"] = None
			base.DATA["Portal"]["Vehicle"] = None
			self.ST_Active_Set()

	def doUpdate(self, world=True):
		owner = self.objects["Root"]

		self.data["LINVEL"] = self.vecTuple(owner.localLinearVelocity)
		self.data["ANGVEL"] = self.vecTuple(owner.localAngularVelocity)

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

		self.cam_slow = []

	def getConstraint(self):
		owner = self.objects["Root"]

		if hasattr(constraints, "createVehicle") == True:
			vehicle = constraints.createVehicle(owner.getPhysicsId())
			self.cid = vehicle.getConstraintId()
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

	def alignObject(self, offset=0.5, velocity=True):
		owner = self.objects["Root"]
		if owner.worldOrientation[2][2] < 0.5:
			owner.alignAxisToVect((0,0,1), 2, 1.0)
			owner.worldPosition[2] += offset
			if velocity == True:
				owner.localLinearVelocity = (0,0,0)
				owner.localAngularVelocity = (0,0,0)
			return True
		return False

	def setPlayerVisibility(self, seat, vis=None):
		if self.driving_player == None:
			return
		if vis == None:
			if self.data["CAMERA"]["State"] == 1:
				vis = False
			else:
				vis = True
			
		for child in seat.childrenRecursive:
			if child == self.driving_player.objects["Mesh"]:
				child.setVisible(vis, False)
			else:
				child.setVisible(False, False)

	def setCamera(self, CAM=0):
		self.objects["CamThird"]["Cam"].timeOffset = self.CAMTHIRD["SLOW"]
		self.objects["CamFirst"]["Loc"].localOrientation = self.createMatrix()
		self.objects["CamFirst"]["Rot"].localOrientation = self.createMatrix()
		self.data["CAMERA"]["Dist"] = self.data["CAMERA"]["Zoom"]

		if CAM == 0:
			CAM = self.data["CAMERA"]["State"]

		if CAM == 3:
			base.SC_SCN.active_camera = self.objects["CamThird"]["Cam"]
			self.setPlayerVisibility(self.objects["Seat"]["1"], True)
			#self.objects["Seat"]["1"].setVisible(True, True)
			self.data["CAMERA"]["State"] = 3

		elif CAM == 1:
			base.SC_SCN.active_camera = self.objects["CamFirst"]["Cam"]
			self.setPlayerVisibility(self.objects["Seat"]["1"], False)
			#self.objects["Seat"]["1"].setVisible(False, True)
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

		## Slow Cam ##
		#if self.CAMTHIRD["SLOW"] > 1:
		#	self.cam_slow.append(self.objects["Root"].worldOrientation.copy())
		#	if len(self.cam_slow) > abs(self.CAMTHIRD["SLOW"]):
		#		self.cam_slow.pop(0)
		#	self.objects["CamThird"]["Loc"].worldOrientation = self.cam_slow[0]


		## Toggle Orbit ##
		if self.data["CAMERA"]["Orbit"] == None:

			if keymap.BINDS["CAM_ORBIT"].tap() == True:
				keymap.MOUSELOOK.center()
				self.data["CAMERA"]["Orbit"] = self.CAMTHIRD["SLOW"]

			#wp = self.objects["Root"].worldPosition
			#wv = self.objects["Root"].worldLinearVelocity
			#self.objects["CamThird"]["Loc"] = wp-(wv*0.05)

		else:
			X, Y = keymap.MOUSELOOK.axis()

			self.objects["CamFirst"]["Loc"].applyRotation((0,0,X), True)
			self.objects["CamFirst"]["Rot"].applyRotation((Y,0,0), True)

			if keymap.BINDS["CAM_ORBIT"].tap() == True:
				keymap.MOUSELOOK.center()
				self.data["CAMERA"]["Orbit"] = None
				self.objects["CamThird"]["Cam"].timeOffset = self.CAMTHIRD["SLOW"]
				self.objects["CamFirst"]["Loc"].localOrientation = self.createMatrix()
				self.objects["CamFirst"]["Rot"].localOrientation = self.createMatrix()

			else:
				self.objects["CamThird"]["Cam"].timeOffset = self.data["CAMERA"]["Orbit"]
				self.data["CAMERA"]["Orbit"] -= self.data["CAMERA"]["Orbit"]*(1/self.CAMTHIRD["SLOW"])
				if self.data["CAMERA"]["Orbit"] < 0:
					self.data["CAMERA"]["Orbit"] = 0

			self.objects["CamThird"]["Loc"].localOrientation = self.objects["CamFirst"]["Loc"].localOrientation.copy()
			self.objects["CamThird"]["Rot"].localOrientation = self.objects["CamFirst"]["Rot"].localOrientation.copy()

			#wp = self.objects["Root"].worldPosition
			#self.objects["CamThird"]["Loc"] = wp

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
		KB = keymap.BINDS
		X, Y = keymap.MOUSELOOK.axis()
		X *= 10
		if X > 1:
			X = 1
		Y *= 10
		if Y > 1:
			Y = 1

		STRAFE = KB["VEH_STRAFERIGHT"].axis(True, clip=True) - KB["VEH_STRAFELEFT"].axis(True, clip=True)
		POWER = KB["VEH_THROTTLEUP"].axis(True, clip=True) - KB["VEH_THROTTLEDOWN"].axis(True, clip=True)
		CLIMB = KB["VEH_ASCEND"].axis(True, clip=True) - KB["VEH_DESCEND"].axis(True, clip=True)

		self.motion["Force"][0] = STRAFE
		self.motion["Force"][1] = POWER
		self.motion["Force"][2] = CLIMB

		PITCH = KB["VEH_PITCHUP"].axis(True, clip=True) - KB["VEH_PITCHDOWN"].axis(True, clip=True)
		BANK = KB["VEH_BANKRIGHT"].axis(True, clip=True) - KB["VEH_BANKLEFT"].axis(True, clip=True)
		YAW = KB["VEH_YAWLEFT"].axis(True, clip=True) - KB["VEH_YAWRIGHT"].axis(True, clip=True)

		self.motion["Torque"][0] = PITCH
		self.motion["Torque"][1] = BANK
		self.motion["Torque"][2] = YAW

		if keymap.SYSTEM["SCREENSHOT"].tap() == True:
			self.doScreenshot()

	def checkClicked(self, OBJ=None):
		if OBJ == None:
			OBJ = self.objects["Root"]

		if OBJ["RAYCAST"] != None:
			if keymap.BINDS["ENTERVEH"].tap() == True or keymap.BINDS["ACTIVATE"].tap() == True:
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
		if self.data["PORTAL"] == False:
			if self.alignObject() == True:
				return
		self.setCamera()
		self.driving_player = self.objects["Root"]["RAYCAST"]
		self.driving_player.enterVehicle(self.objects["Seat"]["1"], self.PLAYERACTION)
		logic.HUDCLASS.setControl(self)
		self.setPlayerVisibility(self.objects["Seat"]["1"])
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
		self.checkStability(True, override=(keymap.SYSTEM["STABILITY"].tap() and self.driving_player) )


class LayoutCar(HUD.HUDLayout):

	GROUP = "Core"
	MODULES = [HUD.Stats, HUD.Speedometer]

class CoreCar(CoreVehicle):

	AIRCONTROL = 0
	CAMTHIRD = {"DIST":8, "ZRATIO":0.2, "MIN":1, "SLOW":20, "RANGE":(4, 16)}
	DRIVECONFIG = {"POWER":100, "SPEED":2, "BRAKE":(1,2), "STEER":1, "DRIVE":0}
	HUDLAYOUT = LayoutCar

	def defaultData(self):
		dict = {}
		dict["ENGINE"] = {
			"Gear":"D",
			"Power":self.DRIVECONFIG["POWER"],
			"Speed":self.DRIVECONFIG["SPEED"]
			}

		return dict

	def ST_Active(self):
		self.doCameraState()
		self.doCameraCollision()
		self.getInputs()

		owner = self.objects["Root"]
		engine = self.data["ENGINE"]

		vel = owner.localLinearVelocity
		speed = abs(vel[1])

		## Steering Optimizer ##
		STEER = 0.8

		if speed > 6:
			STEER = (3/(speed*0.5))*0.8

		STEER = STEER*self.DRIVECONFIG["STEER"]*self.motion["Torque"][2]
		POWER = 0
		BRAKE = 0

		## Gas Pedal ##
		if keymap.BINDS["VEH_THROTTLEUP"].active() == True:
			if vel[1] < -1:
				BRAKE = 2
				engine["Gear"] = "N"
			else:
				POWER = 1
				engine["Gear"] = "D"

		## Brake Pedal ##
		elif keymap.BINDS["VEH_THROTTLEDOWN"].active() == True:
			if vel[1] > 1:
				BRAKE = 1
				engine["Gear"] = "N"
			else:
				POWER = -0.5
				engine["Gear"] = "R"

		HANDBRAKE = 0
		if keymap.BINDS["VEH_HANDBRAKE"].active() == True:
			HANDBRAKE = 2

		## Reset ##
		if keymap.BINDS["VEH_ACTION"].tap() == True:
			self.alignObject()

		FORCE_F = (-engine["Power"] + (speed*engine["Speed"]))*POWER
		DRIVE = self.DRIVECONFIG["DRIVE"]

		## Apply Engine Force ##
		if DRIVE == 0:
			self.vehicle_constraint.applyEngineForce(FORCE_F, 0)
			self.vehicle_constraint.applyEngineForce(FORCE_F, 1)
			self.vehicle_constraint.applyEngineForce(0.0, 2)
			self.vehicle_constraint.applyEngineForce(0.0, 3)
		else:
			if STEER > 0.05:
				self.vehicle_constraint.applyEngineForce(FORCE_F, 2)
				self.vehicle_constraint.applyEngineForce(0.0, 3)
			elif STEER < -0.05:
				self.vehicle_constraint.applyEngineForce(0.0, 2)
				self.vehicle_constraint.applyEngineForce(FORCE_F, 3)
			else:
				self.vehicle_constraint.applyEngineForce(FORCE_F, 2)
				self.vehicle_constraint.applyEngineForce(FORCE_F, 3)

			if DRIVE == 2:
				self.vehicle_constraint.applyEngineForce(FORCE_F, 0)
				self.vehicle_constraint.applyEngineForce(FORCE_F, 1)
			else:
				self.vehicle_constraint.applyEngineForce(0.0, 0)
				self.vehicle_constraint.applyEngineForce(0.0, 1)

		if self.AIRCONTROL != 0:
			owner.applyTorque((self.motion["Torque"][0]*self.AIRCONTROL, self.motion["Torque"][1]*self.AIRCONTROL, 0), True)

		BRAKE = BRAKE*self.DRIVECONFIG["BRAKE"][0]
		HANDBRAKE = HANDBRAKE*self.DRIVECONFIG["BRAKE"][1]

		## Brake All Wheels ##
		self.vehicle_constraint.applyBraking(BRAKE, 0)
		self.vehicle_constraint.applyBraking(BRAKE, 1)
		self.vehicle_constraint.applyBraking(BRAKE, 2)
		self.vehicle_constraint.applyBraking(BRAKE, 3)

		## Brake Rear Wheels ##
		self.vehicle_constraint.applyBraking(HANDBRAKE, 2)
		self.vehicle_constraint.applyBraking(HANDBRAKE, 3)

		## Steer Front Wheels ##
		self.vehicle_constraint.setSteeringValue(STEER, 0)
		self.vehicle_constraint.setSteeringValue(STEER, 1)

		self.data["HUD"]["Text"] = str(round(speed, 1))

		if keymap.BINDS["ENTERVEH"].tap() == True:
			self.ST_Idle_Set()

	def ST_Idle(self):
		owner = self.objects["Root"]

		if self.vehicle_constraint != None:
			self.vehicle_constraint.applyEngineForce(0.0, 0)
			self.vehicle_constraint.applyEngineForce(0.0, 1)
			self.vehicle_constraint.applyEngineForce(0.0, 2)
			self.vehicle_constraint.applyEngineForce(0.0, 3)

			self.vehicle_constraint.applyBraking(self.DRIVECONFIG["BRAKE"][0], 0)
			self.vehicle_constraint.applyBraking(self.DRIVECONFIG["BRAKE"][0], 1)
			self.vehicle_constraint.applyBraking(0.0, 2)
			self.vehicle_constraint.applyBraking(0.0, 3)

		if self.checkClicked() == True:
			self.ST_Active_Set()


class LayoutAircraft(HUD.HUDLayout):

	GROUP = "Core"
	MODULES = [HUD.Stats, HUD.Aircraft]

class CoreAircraft(CoreVehicle):

	LANDACTION = "AircraftRigLand"
	LANDFRAMES = [0, 100]
	AERO = {"POWER":1000, "HOVER":0, "LIFT":0.1, "TAIL":10, "DRAG":(1,1,1)}
	HUDLAYOUT = LayoutAircraft

	def defaultData(self):
		self.lift = 0

		dict = {}
		dict["POWER"] = 0
		dict["HOVER"] = [0,0]
		dict["HUD"] = {"Power":0, "Lift":0}

		return dict

	def airDrag(self):

		dampLin = 0.0
		dampRot = (self.objects["Root"].localLinearVelocity[1]*0.002)+0.4

		if dampRot >= 0.7:
			dampRot = 0.7

		self.objects["Root"].setDamping(dampLin, dampRot)

		self.doDragForce()

	def airLift(self):
		owner = self.objects["Root"]
		linV = owner.localLinearVelocity
		speed = linV.length
		grav = -owner.scene.gravity[2]

		if speed > 0.1 and self.AERO["TAIL"] > 0:
			axis = owner.getAxisVect(linV.normalized())
			factor = self.AERO["TAIL"]/speed
			if factor > 1:
				factor = 1
			owner.alignAxisToVect(axis, 1, factor*0.5)

		self.lift = (linV[1])*self.AERO["LIFT"]*owner.mass
		mass = owner.mass*grav

		if self.lift > mass:
			self.lift = mass

		owner.applyForce((0,0,self.lift), True)

		owner["LIFT"] = self.lift
		owner.addDebugProperty("LIFT", True)

	def getEngineForce(self):
		owner = self.objects["Root"]

		force = self.motion["Force"]
		torque = self.motion["Torque"]
		grav = -owner.scene.gravity[2]
		mass = owner.mass

		self.data["POWER"] += force[1]*(self.AERO["POWER"]/100)
		if self.data["POWER"] > self.AERO["POWER"]:
			self.data["POWER"] = self.AERO["POWER"]

		maxR = self.AERO["POWER"]/4
		if self.data["POWER"] < -maxR:
			self.data["POWER"] = -maxR
		elif self.data["POWER"] < 0:
			if force[1] > -0.1:
				self.data["POWER"] += (self.AERO["POWER"]/100)
				if self.data["POWER"] > 0:
					self.data["POWER"] = 0

		self.data["HOVER"][0] += force[2]*20
		if self.data["HOVER"][0] > 1000 or self.data["HOVER"][1] > 0:
			self.data["HOVER"][0] = 1000
			if force[2] > 0.1:
				self.data["HOVER"][1] += force[2]*20
				if self.data["HOVER"][1] > self.AERO["HOVER"]:
					self.data["HOVER"][1] = self.AERO["HOVER"]
			else:
				self.data["HOVER"][1] -= 20
				if self.data["HOVER"][1] < 0:
					self.data["HOVER"][1] = 0

		if self.data["HOVER"][0] < 0:
			self.data["HOVER"][0] = 0

		## FORCES ##
		power = self.data["POWER"]
		normal = self.data["HOVER"][0]/1000
		base = normal*grav*mass
		hover = ( (base-(self.lift*normal)) + self.data["HOVER"][1] )

		return power, hover

	def doDragForce(self, drag=None, scale=1.0):
		linV = self.objects["Root"].localLinearVelocity
		mass = abs(linV[1])
		if drag == None:
			drag = self.AERO["DRAG"]
		DRAG_X = linV[0]*drag[0]*mass
		DRAG_Y = linV[1]*drag[1]*mass
		DRAG_Z = linV[2]*drag[2]*mass

		self.objects["Root"].applyForce((-DRAG_X, -DRAG_Y, -DRAG_Z), True)

	def doLandingGear(self, init=False):
		start, end = self.LANDFRAMES

		if init == True:
			self.active_post.append(self.doLandingGear)
			self.data["LANDFRAME"] = self.data.get("LANDFRAME", 0)
			self.data["LANDSTATE"] = self.data.get("LANDSTATE", "LAND")

		if self.data["LANDSTATE"] == "LAND":
			if init == True:
				self.doAnim(NAME=self.LANDACTION, FRAME=(start,start))
				return
			if self.data["LANDFRAME"] == 100:
				self.doAnim(NAME=self.LANDACTION, FRAME=(end,start))
			if self.data["LANDFRAME"] == 1:
				self.createVehicle()
			if self.data["LANDFRAME"] != 0:
				self.data["LANDFRAME"] -= 1

		elif self.data["LANDSTATE"] == "FLY":
			if init == True:
				self.doAnim(NAME=self.LANDACTION, FRAME=(end,end))
				return
			if self.data["LANDFRAME"] == 0:
				self.doAnim(NAME=self.LANDACTION, FRAME=(start,end))
				self.removeVehicle()
			if self.data["LANDFRAME"] != abs(end-start):
				self.data["LANDFRAME"] += 1

		if self.driving_player == None:
			return

		owner = self.objects["Root"]
		rayto = list(owner.worldPosition)
		rayto[2] -= 1
		dist = self.WHEELSETUP["HEIGHT"]+self.WHEELSETUP["LENGTH"]+self.WHEELOBJECT["RADIUS"]
		ground = owner.rayCastTo(rayto, dist, "GROUND")

		if keymap.BINDS["TOGGLEMODE"].tap() == True and ground == None:
			if self.data["LANDSTATE"] == "LAND" and self.data["LANDFRAME"] == 0:
				self.data["LANDSTATE"] = "FLY"
			elif self.data["LANDSTATE"] == "FLY" and self.data["LANDFRAME"] == abs(end-start):
				self.data["LANDSTATE"] = "LAND"



