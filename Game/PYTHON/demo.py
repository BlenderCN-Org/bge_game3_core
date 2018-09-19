
## GAME OBJECTS ##


from bge import logic

import PYTHON.base as base
import PYTHON.keymap as keymap

import PYTHON.attachment as attachment
import PYTHON.weapon as weapon
import PYTHON.vehicle as vehicle


class JetPack(attachment.CoreAttachment):

	NAME = "JetPack"
	SLOTS = ["Back"]
	SCALE = 0.74
	OFFSET = (0, 0.0, 0.0)
	ENABLE = True
	POWER = 16
	FUEL = 10000
	BURNRATE = 30
	CHARGERATE = 17

	def defaultData(self):
		self.power = self.createVector(3)
		dict = {"FUEL":self.FUEL}
		return dict

	def doEffects(self, state=None):
		if state in ["INIT", "STOP"]:
			self.randlist = [0]*3
			self.objects["Fire"].localScale = (1, 1, 0)
			return

		rand = 0

		for i in self.randlist:
			rand += i
		rand = (rand/3)

		self.objects["Fire"].localScale = (1, 1, rand)

		self.randlist.insert(0, (logic.getRandomFloat()*0.25)+self.power.length)
		self.randlist.pop()

	def ST_Startup(self):
		self.doEffects("INIT")

	def ST_Stop(self):
		self.doEffects("STOP")
		self.data["HUD"]["Stat"] = int( (self.data["FUEL"]/self.FUEL)*100 )
		self.data["HUD"]["Text"] = str(self.data["HUD"]["Stat"])

		if self.owning_player.jump_state == "JETPACK":
			self.owning_player.jump_state = "B_JUMP"

	## STATE IDLE ##
	def ST_Idle(self):
		plr = self.owning_player
		owner = self.objects["Root"]

		if self.data["ENABLE"] == False:
			self.ST_Stop()
			return

		self.power[0] = 0
		self.power[1] = 0
		self.power[2] = 0

		if plr.jump_state == "B_JUMP" and plr.objects["Root"] != None:
			plr.jump_state = "JETPACK"

		if plr.jump_state == "JETPACK":
			if self.data["FUEL"] > 0:
				self.power[2] = 1

				if plr.motion["Move"].length > 0.01:
					move = plr.motion["Move"].normalized()
					mref = plr.objects["VertRef"].getAxisVect((move[0], move[1], 0))
					self.power[0] = mref[0]
					self.power[1] = mref[1]

					self.power.normalize()

				plr.alignPlayer(factor=0.1)

				plr.objects["Root"].applyForce(self.power*self.POWER, False)
				self.data["FUEL"] -= self.BURNRATE
			else:
				plr.jump_state = "B_JUMP"

		elif plr.jump_state == "FLYING" and keymap.BINDS["PLR_JUMP"].active() == True:
			if self.data["FUEL"] > 0:
				self.power[2] = 1
				plr.objects["Root"].applyForce(self.power*self.POWER, True)
				self.data["FUEL"] -= self.BURNRATE

		else:
			self.randlist = [0]*3
			if self.data["FUEL"] < self.FUEL:
				self.data["FUEL"] += self.CHARGERATE
			else:
				self.data["FUEL"] = self.FUEL

		if self.data["FUEL"] < 0:
			self.data["FUEL"] = 0

		self.data["HUD"]["Stat"] = int( (self.data["FUEL"]/self.FUEL)*100 )
		self.data["HUD"]["Text"] = str(self.data["HUD"]["Stat"])

		self.doEffects()


class DemoStaff(weapon.BasicStaff):

	NAME = "Simple Pole Staff"
	SLOTS = ["Shoulder_R", "Shoulder_L"]
	TYPE = "MELEE"
	OFFSET = (0.1, 0.0, 0.28)
	SCALE = 1.9


class Lightsaber(weapon.BasicSword):

	NAME = "Lightsaber"
	OFFSET = (0,0,0)
	SCALE = 0.4
	WAIT = 15
	BLADETYPE = "GFX_LightSaber.Blade"
	BLADECOLOR = (1,1,1,1)
	BLADESIZE = 1

	def manageBlade(self):
		blade = self.objects["Blade"]

		if self.data["ENABLE"] == True:
			self.gfx_blade.visible = self.objects["Root"].visible
		else:
			self.gfx_blade.visible = False

		if self.active_state == self.ST_Active:
			blade.localScale[1] = 1
		elif self.active_state == self.ST_Draw:
			scale = abs(self.data["COOLDOWN"])/self.WAIT
			blade.localScale[1] = scale
		elif self.active_state == self.ST_Sheath:
			scale = abs(self.data["COOLDOWN"])/self.WAIT
			blade.localScale[1] = 1-scale
		else:
			blade.localScale[1] = 0

	def addBlade(self):
		blade = self.objects["Blade"]
		self.gfx_blade = blade.scene.addObject(self.BLADETYPE, blade, 0)
		self.gfx_blade.setParent(blade)
		self.gfx_blade.color = self.BLADECOLOR
		self.gfx_blade.visible = False
		self.gfx_blade["SIZE"] = self.BLADESIZE
		self.gfx_blade.localPosition = (0,0,0)
		self.gfx_blade.localOrientation = self.createMatrix()
		blade.localScale = (1,0,1)

	def ST_Startup(self):
		self.addBlade()
		self.active_post.append(self.manageBlade)


class LightsaberO(Lightsaber):

	NAME = "Knights' Lightsaber"
	BLADECOLOR = (0,0.3,1,1)

class LightsaberW(Lightsaber):

	NAME = "Masters' Lightsaber"
	BLADECOLOR = (0.4,0,1,1)

class LightsaberV(Lightsaber):

	NAME = "Ergonomic Lightsaber"
	BLADETYPE = "GFX_LightSaber.BladeToon"
	BLADECOLOR = (1,0,0,1)
	BLADESIZE = 0.8


class Buggy(vehicle.CoreCar):

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

