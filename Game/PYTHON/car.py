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

## CAR CLASS ##


from bge import logic

import PYTHON.vehicle as vehicle
import PYTHON.keymap as keymap


## BASE CLASS ##
class CoreCar(vehicle.CoreVehicle):

	AIRCONTROL = 0
	CAMTHIRD = {"DIST":8, "ZRATIO":0.2, "MIN":1, "SLOW":20, "RANGE":(4, 16)}
	DRIVECONFIG = {"POWER":100, "SPEED":2, "BRAKE":(1,2), "STEER":1, "DRIVE":0}

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
			if owner.worldOrientation[2][2] < 0.5:
				owner.alignAxisToVect((0,0,1), 2, 1.0)
				owner.worldPosition[2] += 0.5
				owner.localLinearVelocity = (0,0,0)
				owner.localAngularVelocity = (0,0,0)


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


## CAR TYPES ##
class Mercedes(CoreCar):

	NAME = "Raptor's Mercedes"
	PLAYERACTION = "SeatLow"
	WHEELOBJECT = {"MESH":"Wheel.Mercedes", "RADIUS":0.30}
	WHEELSETUP = {"FRONT":1.275, "REAR":-1.24, "WIDTH":0.75, "HEIGHT":0.35, "LENGTH":0.05}
	WHEELCONFIG = {"ROLL":0.15, "SPRING":120, "DAMPING":12, "FRICTION":5}
	DRIVECONFIG = {"POWER":100, "SPEED":1.75, "BRAKE":(1,1), "STEER":1, "DRIVE":0}
	CAMFIRST = {"POS":(-0.39, -0.45, 0.3)}


class Corvette(CoreCar):

	NAME = "Hugo's Corvette"
	PLAYERACTION = "SeatLow"
	WHEELOBJECT = {"MESH":"Wheel.Corvette", "RADIUS":0.35}
	WHEELSETUP = {"FRONT":1.275, "REAR":-1.35, "WIDTH":0.75, "HEIGHT":0.35, "LENGTH":0.03}
	WHEELCONFIG = {"ROLL":0.15, "SPRING":150, "DAMPING":12, "FRICTION":5}
	DRIVECONFIG = {"POWER":110, "SPEED":1.75, "BRAKE":(1,1), "STEER":1, "DRIVE":1}
	CAMFIRST = {"POS":(-0.39, -0.45, 0.3)}


class Van(CoreCar):

	NAME = "RayBase Transport Van"
	PLAYERACTION = "SeatTall"
	WHEELOBJECT = {"MESH":"Wheel.Van", "RADIUS":0.4}
	WHEELSETUP = {"FRONT":1.87, "REAR":-1.70, "WIDTH":0.8, "HEIGHT":0.8, "LENGTH":0.15}
	WHEELCONFIG = {"ROLL":0.15, "SPRING":120, "DAMPING":10, "FRICTION":5}
	DRIVECONFIG = {"POWER":90, "SPEED":1.5, "BRAKE":(1,1), "STEER":1, "DRIVE":1}
	CAMFIRST = {"POS":(-0.56, 0.9, 0.525)}


class Lamborghini(CoreCar):

	NAME = "Lamborghini"
	PLAYERACTION = "SeatLow"
	WHEELOBJECT = {"MESH":"Wheel.Corvette", "RADIUS":0.33, "COLOR":(0.55, 0.5, 0.45, 1)}
	WHEELSETUP = {"FRONT":1.275, "REAR":-1.48, "WIDTH":0.87, "HEIGHT":0.32, "LENGTH":0.03}
	WHEELCONFIG = {"ROLL":0.15, "SPRING":150, "DAMPING":10, "FRICTION":5}
	DRIVECONFIG = {"POWER":150, "SPEED":2, "BRAKE":(1,1), "STEER":1, "DRIVE":1}
	CAMFIRST = {"POS":(-0.3, 0, 0.3)}


class Silverado(CoreCar):

	NAME = "The Scientist's Truck"
	PLAYERACTION = "SeatTall"
	WHEELOBJECT = {"MESH":"Wheel.Silverado", "RADIUS":0.38}
	WHEELSETUP = {"FRONT":2.13, "REAR":-1.78, "WIDTH":0.85, "HEIGHT":0.3, "LENGTH":0.4}
	WHEELCONFIG = {"ROLL":0.2, "SPRING":150, "DAMPING":20, "FRICTION":5}
	DRIVECONFIG = {"POWER":100, "SPEED":2, "BRAKE":(1,1), "STEER":1, "DRIVE":2}
	CAMFIRST = {"POS":(-0.4, 0.85, 0.45)}


class ATV(CoreCar):

	NAME = "ShowStealer ATV"
	AIRCONTROL = 2
	PLAYERACTION = "SeatRide"
	WHEELOBJECT = {"MESH":"Wheel.ATV", "RADIUS":0.30}
	WHEELSETUP = {"FRONT":0.75, "REAR":-0.75, "WIDTH":0.45, "HEIGHT":0.0, "LENGTH":0.5}
	WHEELCONFIG = {"ROLL":0.1, "SPRING":65, "DAMPING":8, "FRICTION":3}
	DRIVECONFIG = {"POWER":15, "SPEED":0.5, "BRAKE":(0.2,0.1), "STEER":0.8, "DRIVE":0}
	CAMFIRST = {"POS":(0, 0.15, 0.7)}


class Buggy(CoreCar):

	NAME = "All-Terrain Buggy"
	PLAYERACTION = "SeatLow"
	WHEELOBJECT = {"MESH":"Wheel.Buggy", "RADIUS":0.35}
	WHEELSETUP = {"FRONT":1.5, "REAR":-1.5, "WIDTH":1.1, "HEIGHT":0.2, "LENGTH":0.4}
	WHEELCONFIG = {"ROLL":0.1, "SPRING":40, "DAMPING":15, "FRICTION":7}
	DRIVECONFIG = {"POWER":20, "SPEED":0.5, "BRAKE":(0.5,0.2), "STEER":1.2, "DRIVE":2}
	CAMFIRST = {"POS":(0, -0.05, 0.6)}

	def ST_Startup(self):
		self.active_pre.append(self.doSuspensionRig)

	def createVehicle(self):
		self.vehicle_constraint = self.getConstraint()

		setup = self.WHEELSETUP

		FR = self.addWheel((setup["WIDTH"], setup["FRONT"], setup["HEIGHT"]))
		FL = self.addWheel((-setup["WIDTH"], setup["FRONT"], setup["HEIGHT"]))
		RR = self.addWheel((setup["WIDTH"], setup["REAR"], setup["HEIGHT"]))
		RL = self.addWheel((-setup["WIDTH"], setup["REAR"], setup["HEIGHT"]))

		self.objects["WheelObj"] = {"Wheel_FR":FR, "Wheel_FL":FL, "Wheel_RR":RR, "Wheel_RL":RL}

		self.doAnim(OBJECT=self.objects["Rig"], NAME="BuggyRigIdle", MODE="LOOP")

	def doSuspensionRig(self):
		for key in self.objects["WheelObj"]:
			self.objects[key].worldPosition = self.objects["WheelObj"][key].worldPosition.copy()
			self.objects["Rig"].channels[key].location = self.objects[key].localPosition.copy()


