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

from . import base, keymap, HUD, viewport


class CoreVehicle(base.CoreAdvanced):

	NAME = "Vehicle"
	PORTAL = True
	MOUSE_CENTER = True
	MOUSE_SCALE = [100,100]

	WH_OBJECT = "Wheel.None"  # wheel contsraint object
	WH_MESH = None            # Visual wheel object
	WH_RADIUS = 0.2           # Wheel radius
	WH_COLOR = None

	WH_FRONT = 1      # Forward axle offset
	WH_REAR = -1      # Backward axle offset
	WH_WIDTH = 1      # Axle width
	WH_HEIGHT = 0.25  # Axle Z offset

	VEH_LENGTH = 0.25  # Suspension length

	VEH_ROLL = 0.1
	VEH_SPRING = 50
	VEH_DAMPING = 10
	VEH_FRICTION = 5

	WHEELS = {
		"Wheel_FR": {"STEER":True},
		"Wheel_FL": {"LEFT":True, "SCALE":True},
		"Wheel_RR": {"REAR":True},
		"Wheel_RL": {"REAR":True, "LEFT":True, "SCALE":True} }

	SEATS = {
		"Seat_1": {"NAME":"Driver", "DOOR":"Door_1", "CAMERA":None, "ACTION":"SeatLow", "VISIBLE":True, "SPAWN":[-2,0,0]} }

	def __init__(self):
		owner = logic.getCurrentController().owner

		owner["Class"] = self

		owner["RAYNAME"] = self.NAME

		self.objects = {"Root":owner}

		self.defaultStates()

		self.driving_player = owner.get("RAYCAST", None)
		self.driving_seat = None

		self.vehicle_constraint = None
		self.wheel_id = []
		self.id_range = []
		self.wheelobj = {}
		self.seatobj = {}
		self.doorobj = {}
		self.cid = 999

		self.dict = owner["DICT"]
		self.data = self.defaultData()

		self.data["HEALTH"] = 100
		self.data["ENERGY"] = 100
		self.data["HUD"] = {"Text":"", "Color":(0,0,0,0.5), "Target":None}
		self.data["PORTAL"] = False
		self.data["LINVEL"] = (0,0,0)
		self.data["ANGVEL"] = (0,0,0)

		self.motion = {"Force": self.createVector(), "Torque": self.createVector()}

		self.addCollisionCallBack()

		self.checkGhost(owner)
		self.findObjects(owner, ground=False)
		self.findSeats()
		self.doLoad()
		self.createVehicle()
		self.ST_Startup()
		self.doPortal()

		self.loadInventory(owner)

	def defaultStates(self):
		self.active_pre = []
		self.active_state = self.ST_Idle
		self.active_post = [self.PS_SuspensionRig]

	def doPortal(self):
		owner = self.objects["Root"]

		if self.data["PORTAL"] == True:
			door = base.DATA["Portal"]["Door"]
			zone = base.DATA["Portal"]["Zone"]
			portal = owner.scene.objects.get(str(door), None)

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

			owner.localLinearVelocity = self.data["LINVEL"]
			owner.localAngularVelocity = self.data["ANGVEL"]

			base.DATA["Portal"]["Door"] = None
			base.DATA["Portal"]["Zone"] = None
			base.DATA["Portal"]["Vehicle"] = None

			self.driving_seat = self.data["ACTIVE_SEAT"]

			self.ST_Active_Set()
			viewport.updateCamera(self, owner, load=True)

	def doUpdate(self):
		owner = self.objects["Root"]

		self.data["LINVEL"] = self.vecTuple(owner.localLinearVelocity)
		self.data["ANGVEL"] = self.vecTuple(owner.localAngularVelocity)

		self.data["ACTIVE_SEAT"] = self.driving_seat

		if self.driving_player != None:
			self.data["PORTAL"] = True
			base.LEVEL["PLAYER"]["POS"] = self.vecTuple(owner.worldPosition)
			base.LEVEL["PLAYER"]["ORI"] = self.matTuple(owner.worldOrientation)
			base.DATA["Portal"]["Vehicle"] = self.dict

		else:
			self.saveWorldPos()

			if self.UPDATE == True and self.dict not in base.LEVEL["DROP"]:
				base.LEVEL["DROP"].append(self.dict)

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

	def findSeats(self):
		for key in self.SEATS:
			dict = self.SEATS[key]
			seat = self.objects.get(key, None)
			door = self.objects.get(dict.get("DOOR", None), None)
			if seat != None:
				self.seatobj[key] = seat
			if door != None:
				name = dict.get("NAME", key)
				door["RAYNAME"] = self.NAME+": "+name
				door["RAYCAST"] = door.get("RAYCAST", None)
				self.doorobj[key] = door

		owner = self.objects["Root"]
		if len(self.seatobj) == 0 or len(self.doorobj) == 0:
			owner["RAYCAST"] = owner.get("RAYCAST", None)
			self.seatobj["."] = owner
			self.doorobj["."] = owner

	def createVehicle(self):
		self.vehicle_constraint = self.getConstraint()

		for w in self.WHEELS:
			self.addWheel(w, self.WHEELS[w])

	def removeVehicle(self):
		constraints.removeConstraint(self.cid)

		for w in self.wheelobj:
			self.wheelobj[w].endObject()

		self.vehicle_constraint = None
		self.wheel_id = []
		self.id_range = []
		self.wheelobj = {}
		self.cid = 999

	def addWheel(self, w, dict={}):
		id = len(self.wheel_id)

		R = 0
		S = 1
		X = self.WH_WIDTH
		Y = self.WH_FRONT

		obj = base.SC_SCN.addObject(self.WH_OBJECT, self.objects["Root"], 0)

		if dict.get("LEFT", False) == True:
			X = -X
		if dict.get("CENTER", False) == True:
			X = 0
		if dict.get("REAR", False) == True:
			Y = self.WH_REAR
		if dict.get("ROTATE", False) == True:
			R = 180
		if dict.get("SCALE", False) == True:
			S = -1

		if self.WH_MESH != None:
			msh = base.SC_SCN.addObject(self.WH_MESH, self.objects["Root"], 0)
			msh.setParent(obj)
			msh.localPosition = self.createVector()
			msh.localOrientation = self.createMatrix(rot=(0,0,R))
			msh.localScale = (S,1,1)
			if self.WH_COLOR != None:
				msh.color = self.WH_COLOR

		pos = dict.get("POS", [X, Y, -self.WH_HEIGHT])
		length = dict.get("LENGTH", self.VEH_LENGTH)
		radius = dict.get("RADIUS", self.WH_RADIUS)

		self.vehicle_constraint.addWheel(obj, pos, (0,0,-1), (-1,0,0), length, radius, True)

		self.vehicle_constraint.setRollInfluence(self.VEH_ROLL, id)
		self.vehicle_constraint.setSuspensionStiffness(self.VEH_SPRING, id)
		self.vehicle_constraint.setSuspensionDamping(self.VEH_DAMPING, id)
		self.vehicle_constraint.setTyreFriction(self.VEH_FRICTION, id)
		self.vehicle_constraint.setSuspensionCompression(0, id)

		self.wheel_id.append(w)
		self.id_range.append(id)
		self.wheelobj[w] = obj

		return obj

	def getWheelId(self, wheel, key):
		if wheel == key or wheel == None:
			return True
		elif wheel == "FRONT" and "REAR" not in self.WHEELS[key]:
			return True
		elif wheel == "REAR" and "REAR" in self.WHEELS[key]:
			return True
		return False

	def setWheelSteering(self, value, wheel=None, all=False):
		if self.vehicle_constraint == None:
			return

		for i in self.id_range:
			key = self.wheel_id[i]
			check = False
			steer = 0
			if self.getWheelId(wheel, key) == True:
				check = True
				steer = value
			if all == True or check == True:
				self.vehicle_constraint.setSteeringValue(steer, i)

	def setWheelPower(self, value, wheel=None, all=False):
		if self.vehicle_constraint == None:
			return

		for i in self.id_range:
			key = self.wheel_id[i]
			check = False
			power = 0
			if self.getWheelId(wheel, key) == True:
				check = True
				power = value
			if all == True or check == True:
				self.vehicle_constraint.applyEngineForce(power, i)

	def setWheelBrake(self, value, wheel=None, all=False):
		if self.vehicle_constraint == None:
			return

		for i in self.id_range:
			key = self.wheel_id[i]
			check = False
			brake = 0
			if self.getWheelId(wheel, key) == True:
				check = True
				brake = value
			if all == True or check == True:
				self.vehicle_constraint.applyBraking(brake, i)

	def assignCamera(self):
		viewport.setCamera(self)
		viewport.setParent(self.objects["Root"])

	def hideObject(self):
		self.objects["Root"].setVisible(False, True)
		for w in self.wheelobj:
			self.wheelobj[w].setVisible(False, True)

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

	def setPlayerVisibility(self, vis=None):
		if self.driving_player == None or self.driving_seat == None:
			return

		seat = self.seatobj[self.driving_seat]

		if self.driving_seat == ".":
			vis = False
			seat = self.driving_player.objects["Character"]
		elif vis == None:
			dict = self.SEATS[self.driving_seat]
			vis = dict.get("VISIBLE", True)
			
		for child in seat.childrenRecursive:
			if child == self.driving_player.objects["Mesh"]:
				child.setVisible(vis, False)
			else:
				child.setVisible(False, False)

	def getInputs(self):
		KB = keymap.BINDS

		STRAFE = KB["VEH_STRAFERIGHT"].axis(True, True) - KB["VEH_STRAFELEFT"].axis(True, True)
		POWER = KB["VEH_THROTTLEUP"].axis(True, True) - KB["VEH_THROTTLEDOWN"].axis(True, True)
		CLIMB = KB["VEH_ASCEND"].axis(True, True) - KB["VEH_DESCEND"].axis(True, True)

		self.motion["Force"][0] = STRAFE
		self.motion["Force"][1] = POWER
		self.motion["Force"][2] = CLIMB

		PITCH = KB["VEH_PITCHUP"].axis(True, True) - KB["VEH_PITCHDOWN"].axis(True, True)
		BANK = KB["VEH_BANKRIGHT"].axis(True, True) - KB["VEH_BANKLEFT"].axis(True, True)
		YAW = KB["VEH_YAWLEFT"].axis(True, True) - KB["VEH_YAWRIGHT"].axis(True, True)

		self.data["HUD"]["Target"] = None

		if self.data["CAMERA"]["Orbit"] <= 0:
			X, Y = keymap.MOUSELOOK.axis(ui=True, center=self.MOUSE_CENTER)

			BANK  += X *self.MOUSE_SCALE[0]
			PITCH += Y *self.MOUSE_SCALE[1]

			if abs(BANK) > 1:
				BANK = 1-(2*(BANK<0))
			if abs(PITCH) > 1:
				PITCH = 1-(2*(PITCH<0))

			self.data["HUD"]["Target"] = [BANK, PITCH]

		self.motion["Torque"][0] = PITCH
		self.motion["Torque"][1] = BANK
		self.motion["Torque"][2] = YAW

	def checkClicked(self, OBJ=None):
		for key in self.doorobj:
			obj = self.doorobj[key]
			if obj["RAYCAST"] != None:
				if keymap.BINDS["ENTERVEH"].tap() == True or keymap.BINDS["ACTIVATE"].tap() == True:
					self.driving_player = obj["RAYCAST"]
					self.driving_seat = key
					return True
		return False

	def clearRayProps(self):
		owner = self.objects["Root"]
		for key in self.doorobj:
			obj = self.doorobj[key]
			obj["RAYCAST"] = None

	## IDLE STATE ##
	def ST_Idle(self):
		owner = self.objects["Root"]

		if self.checkClicked() == True:
			self.ST_Active_Set()

	def ST_Idle_Set(self):
		owner = self.objects["Root"]
		if self.driving_seat == ".":
			spawn = self.createVector(vec=(-1,0,0))
		else:
			spawn = self.createVector(vec=self.SEATS[self.driving_seat]["SPAWN"])

		dist = spawn.length
		spawn = self.getWorldSpace(owner, spawn)

		rayOBJ = owner.rayCastTo(spawn, dist+0.5, "GROUND")
		if rayOBJ != None:
			return

		self.driving_player.doAnim(STOP=True)
		self.driving_player.exitVehicle(spawn)
		self.driving_player = None
		self.driving_seat = None
		self.active_state = self.ST_Idle
		self.data["PORTAL"] = False

	## ACTIVE STATE ##
	def ST_Active(self):
		self.getInputs()

		owner = self.objects["Root"]

		if keymap.BINDS["ENTERVEH"].tap() == True:
			self.ST_Idle_Set()

	def ST_Active_Set(self):
		if self.data["PORTAL"] == False:
			if self.alignObject() == True:
				self.driving_player = None
				self.driving_seat = None
				return

		plr = self.driving_player
		key = self.driving_seat
		seat = self.seatobj[key]
		door = self.doorobj[key]

		plr.enterVehicle(seat)
		self.setPlayerVisibility()

		if key == ".":
			action = "Jumping"
		else:
			action = self.SEATS[key].get("ACTION", None)
		plr.doAnim(NAME=action, FRAME=(0,0), MODE="LOOP")

		self.assignCamera()

		HUD.SetLayout(self)

		self.active_state = self.ST_Active
		self.data["PORTAL"] = True

	## RUN ##
	def PS_SuspensionRig(self):
		owner = self.objects["Root"]
		if self.objects.get("Rig", None) == None:
			return "REMOVE"
		for key in self.wheelobj:
			ch = self.objects["Rig"].channels.get(key, None)
			if ch != None:
				pnt = self.wheelobj[key].worldPosition-owner.worldPosition
				lp = owner.worldOrientation.inverted()*pnt
				offset = ch.bone.arm_head
				ch.location = lp-offset

		self.doAnim(OBJECT=self.objects["Rig"], NAME="ArmatureIdle", PRIORITY=3, MODE="LOOP")

	def RUN(self):
		self.runPre()
		self.runStates()
		self.runPost()
		self.clearRayProps()
		self.checkStability(True, override=(keymap.SYSTEM["STABILITY"].tap() and self.driving_player) )


class LayoutCar(HUD.HUDLayout):

	GROUP = "Core"
	MODULES = [HUD.Stats, HUD.Speedometer, HUD.MousePos]

class CoreCar(CoreVehicle):

	MOUSE_CENTER = False
	MOUSE_SCALE = [10,0]

	CAM_HEIGHT = 0.2
	CAM_MIN = 0.7
	CAM_SLOW = 10
	CAM_ORBIT = False

	CAR_POWER = 70
	CAR_SPEED = 100
	CAR_BRAKE = 1
	CAR_HANDBRAKE = 1
	CAR_STEER = 1
	CAR_DRIVE = "FRONT"
	CAR_AIR = (0,0,0)

	DRIVECONFIG = {"POWER":100, "SPEED":2, "BRAKE":(1,1), "STEER":1, "DRIVE":0, "AIR":None}
	HUDLAYOUT = LayoutCar

	def defaultData(self):
		dict = {}
		dict["ENGINE"] = {
			"Power":self.CAR_POWER,
			"Speed":self.CAR_SPEED
			}

		return dict

	def ST_Active(self):
		owner = self.objects["Root"]

		self.getInputs()

		engine = self.data["ENGINE"]
		torque = self.motion["Torque"]

		vel = owner.localLinearVelocity
		speed = abs(vel[1])

		## Steering Optimizer ##
		turn = 0.8

		if speed > 6:
			turn = (3/(speed*0.5))*0.8

		STEER = (torque[1]*-1)+torque[2]
		if abs(STEER) > 1:
			STEER = 1-(2*(STEER<0))
		STEER = self.CAR_STEER*STEER*turn
		POWER = 0
		BRAKE = 0

		## Gas Pedal ##
		if keymap.BINDS["VEH_THROTTLEUP"].active() == True:
			if vel[1] < -1:
				BRAKE = 2
			else:
				POWER = 1

		## Brake Pedal ##
		elif keymap.BINDS["VEH_THROTTLEDOWN"].active() == True:
			if vel[1] > 1:
				BRAKE = 1
			else:
				POWER = -0.5

		HANDBRAKE = 0
		if keymap.BINDS["VEH_HANDBRAKE"].active() == True:
			HANDBRAKE = 2

		## Reset ##
		if keymap.BINDS["VEH_ACTION"].tap() == True:
			self.alignObject()

		mx = 1
		if speed > 0.1:
			mx = 1-(speed/self.CAR_SPEED)

		FORCE_F = (engine["Power"]*mx)*-POWER
		DRIVE = self.CAR_DRIVE

		## Apply Engine Force ##
		if DRIVE == "FRONT":
			self.setWheelPower(FORCE_F, "FRONT", all=True)
		else:
			if STEER > 0.05:
				self.setWheelPower(FORCE_F, "Wheel_RR")
				self.setWheelPower(0.0, "Wheel_RL")
			elif STEER < -0.05:
				self.setWheelPower(0.0, "Wheel_RR")
				self.setWheelPower(FORCE_F, "Wheel_RL")
			else:
				self.setWheelPower(FORCE_F, "REAR")

			if DRIVE == "FOUR":
				self.setWheelPower(FORCE_F, "FRONT")
			else:
				self.setWheelPower(0.0, "FRONT")

		air = self.CAR_AIR
		owner.applyTorque((torque[0]*air[0], torque[1]*air[1], torque[2]*air[2]), True)

		BRAKE = BRAKE*self.CAR_BRAKE
		HANDBRAKE = HANDBRAKE*self.CAR_HANDBRAKE

		## Brake All Wheels ##
		self.setWheelBrake(BRAKE)

		## Brake Rear Wheels ##
		self.setWheelBrake(HANDBRAKE, "REAR")

		## Steer Front Wheels ##
		self.setWheelSteering(STEER, "FRONT")

		self.data["HUD"]["Text"] = str(int(round(speed, 1)))

		if keymap.BINDS["ENTERVEH"].tap() == True:
			self.ST_Idle_Set()

	def ST_Idle(self):
		owner = self.objects["Root"]

		self.setWheelPower(0)
		self.setWheelBrake(self.CAR_BRAKE, "FRONT", all=True)

		if self.checkClicked() == True:
			self.ST_Active_Set()


class LayoutAircraft(HUD.HUDLayout):

	GROUP = "Core"
	MODULES = [HUD.Stats, HUD.Aircraft, HUD.MousePos]

class CoreAircraft(CoreVehicle):

	LANDACTION = "AircraftRigLand"
	LANDFRAMES = [0, 100]

	CAM_HEIGHT = 0.1
	CAM_MIN = 1
	CAM_SLOW = 5

	SEATS = {
		"Seat_1": {"NAME":"Driver", "DOOR":"Root", "CAMERA":None, "ACTION":"SeatLow", "VISIBLE":True, "SPAWN":[-2,0,0]} }

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
		grav = -owner.scene.gravity[2]

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

	def doDragForce(self, drag=None, scale=None):
		linV = self.objects["Root"].localLinearVelocity
		if scale == None:
			scale = abs(linV[1])
		if drag == None:
			drag = self.AERO["DRAG"]
		DRAG_X = linV[0]*drag[0]*scale
		DRAG_Y = linV[1]*drag[1]*scale
		DRAG_Z = linV[2]*drag[2]*scale

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
		dist = self.WH_HEIGHT + self.VEH_LENGTH + self.WH_RADIUS
		ground = owner.rayCastTo(rayto, dist, "GROUND")

		if keymap.BINDS["TOGGLEMODE"].tap() == True and ground == None:
			if self.data["LANDSTATE"] == "LAND" and self.data["LANDFRAME"] == 0:
				self.data["LANDSTATE"] = "FLY"
			elif self.data["LANDSTATE"] == "FLY" and self.data["LANDFRAME"] == abs(end-start):
				self.data["LANDSTATE"] = "LAND"



