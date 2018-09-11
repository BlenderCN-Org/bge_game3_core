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

## AIRCRAFT CLASS ##


from bge import logic

import PYTHON.vehicle as vehicle
import PYTHON.keymap as keymap


## BASE CLASS ##
class CoreAircraft(vehicle.CoreVehicle):

	AERO = {"LIFT":0.1, "DRAG":(1,0.1,1), "ALIGN":10}

	def airDrag(self):

		#dampLin = 0.0
		#dampRot = (self.linV[1]*0.002)+0.4

		#if dampRot >= 0.7:
		#	dampRot = 0.7

		#self.objects["Root"].setDamping(dampLin, dampRot)

		ABS_Y = abs(self.linV[1])

		DRAG_X = self.linV[0]*ABS_Y*self.AERO["DRAG"][0]
		DRAG_Y = self.linV[1]*ABS_Y*self.AERO["DRAG"][1]
		DRAG_Z = self.linV[2]*ABS_Y*self.AERO["DRAG"][2]

		self.objects["Root"].applyForce((-DRAG_X, -DRAG_Y, -DRAG_Z), True)

	def airLift(self):
		owner = self.objects["Root"]
		speed = self.linV.length
		grav = -owner.scene.gravity[2]

		if speed > 0.1:
			axis = owner.getAxisVect((0,1,0))
			factor = self.AERO["ALIGN"]/speed
			if factor > 1:
				factor = 1
			owner.alignAxisToVect(axis, 1, factor*0.5)

		baselift = (self.linV[1]**2)*self.AERO["LIFT"]
		mass = owner.mass*grav
		lift = baselift

		if lift > mass:
			lift = mass

		owner.applyForce((0,0,lift), True)

class FireBird(CoreAircraft):

	NAME = "Raptor's Firebird"
	SPAWN = (-1.5, 2, 0)
	PLAYERACTION = "SeatTall"
	CAMTHIRD = {"DIST":10, "ZRATIO":0.1, "MIN":1, "SLOW":3, "RANGE":(4, 16)}
	WHEELOBJECT = {"MESH":"Wheel.None", "RADIUS":0.2}
	WHEELSETUP = {"FRONT":2.5, "REAR":-1, "WIDTH":0.9, "HEIGHT":0.8, "LENGTH":0.5}
	WHEELCONFIG = {"ROLL":0.0, "SPRING":50, "DAMPING":8, "FRICTION":5}

	def defaultData(self):
		self.lift = 0

		dict = {}
		dict["FLYMODE"] = "LAND"
		dict["POWER"] = 0
		dict["HOVER"] = [0,0]
		dict["GEAR"] = 0

		return dict

	def createVehicle(self):
		if self.data["FLYMODE"] == "FLY":
			return

		self.vehicle_constraint = self.getConstraint()

		setup = self.WHEELSETUP

		self.addWheel((0, setup["FRONT"], setup["HEIGHT"]))

		self.addWheel((setup["WIDTH"], setup["REAR"], setup["HEIGHT"]))
		self.addWheel((-setup["WIDTH"], setup["REAR"], setup["HEIGHT"]))

	def airDrag(self):

		dampLin = 0.0
		dampRot = (self.linV[1]*0.002)+0.4

		if dampRot >= 0.7:
			dampRot = 0.7

		self.objects["Root"].setDamping(dampLin, dampRot)

		ABS_Y = abs(self.linV[1])
		drag = ((100-self.data["GEAR"])*0.001)+0.2

		DRAG_X = self.linV[0]*ABS_Y*1
		DRAG_Y = self.linV[1]*ABS_Y*drag
		DRAG_Z = self.linV[2]*ABS_Y*2

		self.objects["Root"].applyForce((-DRAG_X, -DRAG_Y, -DRAG_Z), True)

	def airLift(self):
		owner = self.objects["Root"]
		speed = self.linV.length
		grav = -owner.scene.gravity[2]

		self.lift = (self.linV[1]**2)*0.2

		if self.lift > 980:
			self.lift = 980

		#self.data["HUD"]["Text"] = str(int(self.lift))

		owner.applyForce((0,0,self.lift*1.5), True)

	def doLandingGear(self, start=False):
		if self.data["FLYMODE"] == "LAND":
			if start == True:
				self.doAnim(NAME="FirebirdRigLand", FRAME=(0,0))
				return
			if self.data["GEAR"] == 100:
				self.doAnim(NAME="FirebirdRigLand", FRAME=(100,0))
			if self.data["GEAR"] == 1:
				self.createVehicle()
			if self.data["GEAR"] != 0:
				self.data["GEAR"] -= 1

		elif self.data["FLYMODE"] == "FLY":
			if start == True:
				self.doAnim(NAME="FirebirdRigLand", FRAME=(100,100))
				return
			if self.data["GEAR"] == 0:
				self.doAnim(NAME="FirebirdRigLand", FRAME=(0,100))
				self.removeVehicle()
			if self.data["GEAR"] != 100:
				self.data["GEAR"] += 1

	def ST_Startup(self):
		self.ANIMOBJ = self.objects["Rig"]
		self.doLandingGear(start=True)
		self.active_post.append(self.doLandingGear)
		self.active_post.append(self.airDrag)
		self.active_post.append(self.airLift)

	## ACTIVE STATE ##
	def ST_Active(self):
		self.doCameraState()
		self.doCameraCollision()
		self.getInputs()

		owner = self.objects["Root"]
		mesh = self.objects["Mesh"]

		force = self.motion["Force"]
		torque = self.motion["Torque"]

		self.data["POWER"] += force[1]*20
		if self.data["POWER"] > 10000:
			self.data["POWER"] = 10000

		if self.data["POWER"] < 0:
			self.data["POWER"] = 0

		self.data["HOVER"][0] += force[2]*20
		if self.data["HOVER"][0] > 980 or self.data["HOVER"][1] > 0:
			self.data["HOVER"][0] = 980
			if force[2] > 0.1:
				self.data["HOVER"][1] += force[2]*20
				if self.data["HOVER"][1] > 500:
					self.data["HOVER"][1] = 500
			else:
				self.data["HOVER"][1] -= 20
				if self.data["HOVER"][1] < 0:
					self.data["HOVER"][1] = 0

		if self.data["HOVER"][0] < 0:
			self.data["HOVER"][0] = 0

		## FORCES ##
		power = self.data["POWER"] - self.linV[1]
		hover = (self.data["HOVER"][0]-(self.lift*(self.data["HOVER"][0]/980))) + self.data["HOVER"][1]
		mx = abs(self.linV[1])

		owner.applyTorque([torque[0]*400, torque[1]*800, torque[2]*400], True)
		owner.applyForce([0.0, power, hover*1.5], True)

		self.data["ENERGY"] = abs(self.data["POWER"]/100)
		self.data["HUD"]["Text"] = str(int(hover))

		## EXTRAS ##
		mesh.color[0] = abs(self.data["POWER"]/10000)
		if mesh.color[1] < 1:
			mesh.color[1] += 0.01
		else:
			mesh.color[1] = 1

		if self.vehicle_constraint != None:
			self.vehicle_constraint.setSteeringValue(torque[2]*0.3, 0)
			if keymap.BINDS["VEH_DESCEND"].active() == True:
				brake = 10
			elif keymap.BINDS["VEH_THROTTLEDOWN"].active() == True and self.data["POWER"] < 1:
				brake = 10
			else:
				brake = 0
			self.vehicle_constraint.applyBraking(brake, 1)
			self.vehicle_constraint.applyBraking(brake, 2)

		## LANDING GEAR ##
		rayto = list(owner.worldPosition)
		rayto[2] -= 1
		ground = owner.rayCastTo(rayto, 2, "GROUND")

		if keymap.BINDS["TOGGLEMODE"].tap() == True and ground == None:
			if self.data["FLYMODE"] == "LAND" and self.data["GEAR"] == 0:
				self.data["FLYMODE"] = "FLY"
			elif self.data["FLYMODE"] == "FLY" and self.data["GEAR"] == 100:
				self.data["FLYMODE"] = "LAND"

		if keymap.BINDS["ENTERVEH"].tap() == True and self.linV.length < 10:
			mesh.color[1] = 0
			self.ST_Idle_Set()

	def ST_Idle(self):
		if self.vehicle_constraint != None:
			self.vehicle_constraint.applyBraking(1.0, 1)
			self.vehicle_constraint.applyBraking(1.0, 2)

		if self.checkClicked() == True:
			self.ST_Active_Set()


class RaynaPod(CoreAircraft):

	NAME = "Rayna's Escape Pod"
	SPAWN = (0, 2, 0)
	PLAYERACTION = "SeatTall"
	CAMFIRST = {"POS":(0,0,0.4)}
	CAMTHIRD = {"DIST":8, "ZRATIO":0.2, "MIN":1, "SLOW":10, "RANGE":(4, 16)}
	WHEELOBJECT = {"MESH":"Wheel.None", "RADIUS":0.2}
	WHEELSETUP = {"FRONT":1, "REAR":-1, "WIDTH":2, "HEIGHT":0.7, "LENGTH":0.3}
	WHEELCONFIG = {"ROLL":0.0, "SPRING":30, "DAMPING":10, "FRICTION":2}

	AERO = {"LIFT":0, "DRAG":(3,0,3), "ALIGN":10}

	def defaultData(self):
		dict = {"FLYMODE":False}
		return dict

	def ST_Startup(self):
		self.objects["CamFirst"]["Loc"].setParent(self.objects["Chair"])
		self.objects["CamThird"]["Loc"].setParent(self.objects["Chair"])
		self.objects["Root"].setDamping(0.1, 0.7)
		self.randlist = [0.1]*5

		self.setFlyMode(start=True)

	def setFlyMode(self, mode=None, start=False):
		if mode == None:
			mode = self.data["FLYMODE"]

		ring = self.objects["Ring"]
		chair = self.objects["Chair"]

		if mode == False:
			frame = (0, 60)
			if start == True:
				frame = (60, 60)
		elif mode == True:
			frame = (60, 0)
			if start == True:
				frame = (0, 0)

		self.doAnim(OBJECT="Wings", NAME="RaypodWingsMode", FRAME=frame)

	def doWheelBrake(self):
		if self.vehicle_constraint != None:
			self.vehicle_constraint.applyEngineForce(0.0, 0)
			self.vehicle_constraint.applyEngineForce(0.0, 1)
			self.vehicle_constraint.applyEngineForce(0.0, 2)
			self.vehicle_constraint.applyEngineForce(0.0, 3)

			self.vehicle_constraint.applyBraking(1.0, 0)
			self.vehicle_constraint.applyBraking(1.0, 1)
			self.vehicle_constraint.applyBraking(1.0, 2)
			self.vehicle_constraint.applyBraking(1.0, 3)

	## ACTIVE STATE ##
	def ST_Active(self):
		self.doCameraState()
		self.doCameraCollision()
		self.getInputs()

		force = self.motion["Force"]
		torque = self.motion["Torque"]

		rand = 0
		for i in self.randlist:
			rand += i
		rand = (rand/5)

		owner = self.objects["Root"]
		ring = self.objects["Ring"]
		chair = self.objects["Chair"]
		wings = self.objects["Wings"]
		fire = self.objects["Fire"]

		if self.data["FLYMODE"] == False:
			owner.applyTorque((torque[0]*100, torque[1]*1000, torque[2]*500), True)

			owner.applyForce((0,0,980+(force[2]*400)), True)

			owner.alignAxisToVect((0,0,1), 2, 0.02)
			ring.alignAxisToVect((0,0,1), 1, 0.2)
			chair.alignAxisToVect((0,0,1), 2, 0.2)

			mxfire = force[2]
			fire.localScale[1] = (0.3+(rand*0.2))

			self.doWheelBrake()

			if keymap.BINDS["TOGGLEMODE"].tap() == True:
				#wings.localOrientation = ((1,0,0),(0,1,0),(0,0,1))
				self.data["FLYMODE"] = True
				self.setFlyMode()

			if keymap.BINDS["ENTERVEH"].tap() == True:
				self.ST_Idle_Set()

		else:
			owner.applyTorque((torque[0]*200, torque[1]*2000, torque[2]*500), True)
			self.airDrag()

			Y = (5000+(force[1]*3000))-self.linV[1]**2

			owner.applyForce((0, Y, force[2]*1000), True)
			owner.applyForce((0,0,980), False)

			yref = owner.getAxisVect((0,1,0))
			ring.alignAxisToVect(yref, 1, 0.2)
			chair.alignAxisToVect(yref, 1, 0.2)

			mxfire = force[1]
			fire.localScale[1] = (1+(rand*0.5))

			if keymap.BINDS["TOGGLEMODE"].tap() == True:
				#wings.localOrientation = ((1,0,0),(0,0,-1),(0,1,0))
				self.data["FLYMODE"] = False
				self.setFlyMode()

		## Reset ##
		if keymap.BINDS["VEH_ACTION"].tap() == True:
			if owner.worldOrientation[2][2] < 0.5:
				owner.alignAxisToVect((0,0,1), 2, 1.0)
				owner.worldPosition[2] += 0.5
				owner.localLinearVelocity = (0,0,0)
				owner.localAngularVelocity = (0,0,0)

		self.randlist.insert(0, logic.getRandomFloat()+mxfire)
		self.randlist.pop()

		zref = wings.getAxisVect((0,0,1))
		ring.alignAxisToVect(zref, 2, 1.0)

		xref = ring.getAxisVect((1,0,0))
		chair.alignAxisToVect(xref, 0, 1.0)

	## IDLE STATE ##
	def ST_Idle(self):

		owner = self.objects["Root"]

		self.objects["Fire"].localScale[1] = -0.1

		self.doWheelBrake()

		if self.checkClicked() == True:
			self.ST_Active_Set()



