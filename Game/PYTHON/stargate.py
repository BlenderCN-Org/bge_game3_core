

from bge import logic

import PYTHON.base as base
import PYTHON.keymap as keymap


if "STARGATE" not in base.LEVEL:
	base.LEVEL["STARGATE"] = {}

ADDRESS = {}

ADDRESS["MILKYWAY"] = {
"1A:1B:1C:1D:1E:1F:1P": "SGC Game",
"2A:2B:2C:2D:2E:2F:1P": "Abydos Game",
"1A:1B:1C:1D:1E:1F:1O:1P": "Midway",
"2A:2B:2C:2D:2E:2F:1O:1P": "Wizards"
}

ADDRESS["PEGASUS"] = {
"1A:1B:1C:1D:1E:1F:1P": "Atlantis Room",
"2A:2B:2C:2D:2E:2F:1P": "Village Game",
"1A:1B:1C:1D:1E:1F:1O:1P": "Midway",
"2A:2B:2C:2D:2E:2F:1O:1P": "Wizards"
}


class IrisControl(base.CoreObject):

	NAME = "Iris Control Switch"
	GALAXY = "MILKYWAY"
	UPDATE = False

	def ST_Startup(self):
		self.objects["Root"].color = (0,0,0,1)
		self.active_state = self.ST_Disabled

	def ST_Active(self):
		owner = self.objects["Root"]
		gate = self.STARGATE["Gate"]["Data"]

		if gate["IRIS"] == "OPEN":
			owner.color[0] = 0
			if self.checkClicked() == True:
				gate["IRIS"] = "CLOSE"

		elif gate["IRIS"] == "CLOSE":
			owner.color[0] = 1
			if self.checkClicked() == True:
				gate["IRIS"] = "OPEN"

		owner["RAYCAST"] = None

	def ST_Disabled(self):
		if self.GALAXY in base.LEVEL["STARGATE"]:
			self.STARGATE = base.LEVEL["STARGATE"][self.GALAXY]
			if self.STARGATE["Gate"] != None:
				self.active_state = self.ST_Active

class CoreGate(base.CoreObject):

	NAME = "Stargate"
	GALAXY = "MILKYWAY"
	GHOST = True

	def ST_Startup(self):
		global ADDRESS

		if self.GALAXY not in base.LEVEL["STARGATE"]:
			base.LEVEL["STARGATE"][self.GALAXY] = {"Gate":None, "DHD":None}

		self.LOOKUP = ADDRESS[self.GALAXY]
		self.STARGATE = base.LEVEL["STARGATE"][self.GALAXY]

		self.STARGATE["Gate"] = self.objects["Root"]["DICT"]

		base.DATA["Portal"]["Stargate"] = base.DATA["Portal"].get("Stargate", "NONE")

		self.ANIMOBJ = self.objects.get("Rig", None)

		self.doAnim(NAME="Chevron", FRAME=(0,0), LAYER=0, MODE="LOOP")

		del self.objects["Root"]["RAYCAST"]

		self.data["ADDRESS"] = []
		self.data["IRIS"] = "OPEN"

		self.active_pre.append(self.ST_Iris)
		self.active_state = self.ST_Disabled

		self.timer = 0
		self.chevron = None
		self.iris_state = "OPEN"
		self.iris_timer = 0
		self.back = []

		self.puddle = None
		self.effect = None

		color = (0,0,0,1)

		if base.DATA["Portal"]["Stargate"] == self.GALAXY:
			self.doTrack("ON")
			self.addPuddle()
			self.ST_Shutdown_Set()
			color = (1,1,1,1)

		for key in self.objects["Chevron"]:
			self.doTrack("START")
			obj = self.objects["Chevron"][key]
			obj.color = color

	def doTrack(self, state):
		pass

	def addPuddle(self):
		scene = base.SC_SCN
		owner = self.objects["Root"]

		self.puddle = scene.addObject("GFX_Puddle", owner, 0)
		self.effect = scene.addObject("GFX_Effect", owner, 0)

		self.puddle.setParent(owner)
		self.effect.setParent(owner)

		self.puddle.color = (1,1,1,0)
		self.effect.color = (1,1,1,1)

		self.setLights("START")

	def doEventHorizon(self, state):

		frame = (0, 60)

		if state == "END":
			self.doTrack("OFF")
			self.setLights("ZERO")

			if self.puddle != None:
				self.puddle.endObject()
				self.puddle = None
			if self.effect != None:
				self.effect.endObject()
				self.effect = None

			return

		if state == "ON" and len(self.data["ADDRESS"]) != 0:

			lookup = ":".join(self.data["ADDRESS"])
			map = self.LOOKUP.get(lookup, "")

			if map+".blend" not in [base.CURRENT["Level"], ""]:
				self.doTrack("ON")
				self.addPuddle()

				self.puddle.localOrientation = self.createMatrix(mirror="XY")
				for child in self.puddle.childrenRecursive:
					child.localPosition[1] *= -1

				self.puddle["MAP"] = map
				self.puddle["COLLIDE"] = []

		if state == "OFF":
			frame = (40, 0)
			self.setLights("END")

		self.doAnim(OBJECT=self.puddle, NAME="PuddleColor", FRAME=frame)
		self.doAnim(OBJECT=self.effect, NAME="EffectColor", FRAME=frame)

	def setLights(self, state):
		if self.puddle == None:
			return

		point_0 = self.puddle.childrenRecursive["GFX_PuddlePoint_0"]
		point_1 = self.puddle.childrenRecursive["GFX_PuddlePoint_1"]

		if state == "ZERO":
			self.doAnim(OBJECT=point_0, NAME="PointEnergy", FRAME=(0,0))
			self.doAnim(OBJECT=point_1, NAME="PointEnergy", FRAME=(0,0))

		if state == "OFF":
			state = 2
			self.doAnim(OBJECT=point_0, NAME="PointEnergy", FRAME=(160,240))

		elif state == "ON":
			state = -2
			self.doAnim(OBJECT=point_0, NAME="PointEnergy", FRAME=(200,160))

		elif state == "END":
			state = 2
			self.doAnim(OBJECT=point_1, NAME="PointEnergy", FRAME=(160,240))
			if self.iris_state != "CLOSED":
				self.doAnim(OBJECT=point_0, NAME="PointEnergy", FRAME=(160,240))

		elif state == "START":
			state = 0
			self.doAnim(OBJECT=point_1, NAME="PointEnergy", FRAME=(0,100))
			if self.iris_state != "CLOSED":
				self.doAnim(OBJECT=point_0, NAME="PointEnergy", FRAME=(0,100))

	def doPuddle(self):
		if self.puddle == None:
			return None

		player = None

		for cls in self.puddle["COLLIDE"]:
			if cls.PORTAL == True:
				vehicle = cls.data.get("PORTAL", None)
				if vehicle != False:
					player = cls

			nrm = self.puddle.getAxisVect([0,-1,0])
			vec = self.puddle.getVectTo(cls.objects["Root"])[1]
			if nrm.dot(vec) < 0.01:
				if cls not in self.back:
					self.back.append(cls)

		clr = []
		for chk in self.back:
			if chk not in self.puddle["COLLIDE"]:
				clr.append(chk)

		if player in self.back:
			player = None

		for i in clr:
			self.back.remove(i)

		self.puddle["COLLIDE"] = []

		if self.iris_state == "OPEN":
			return player
		return None

	def clearRayProps(self):
		return

	def ST_Iris(self):
		pass

	def ST_Shutdown(self):
		self.timer -= 1

		if self.timer < 20:
			for key in self.objects["Chevron"]:
				obj = self.objects["Chevron"][key]
				obj.color[0] = obj.color[0]*(self.timer/20)

		if self.timer == 0:
			self.ST_Disabled_Set()

	def ST_Shutdown_Set(self):
		if self.STARGATE["DHD"] != None:
			self.STARGATE["DHD"]["Data"]["ADDRESS"] = []
		self.data["ADDRESS"] = []
		base.DATA["Portal"]["Stargate"] = "NONE"
		self.timer = 60
		self.active_state = self.ST_Shutdown
		self.doEventHorizon("OFF")

	def ST_Disabled(self):
		if len(self.data["ADDRESS"]) > 0:
			self.ST_Dialing_Set()

	def ST_Dialing_Set(self):
		self.timer = 0
		self.chevron = 1
		self.active_state = self.ST_Dialing

	def ST_Dialing(self):
		id = str(self.chevron)
		obj = self.objects["Chevron"][id]

		if self.timer < 200:
			self.doTrack("DIALING")

		if self.timer == 200:
			self.doAnim(NAME=id, FRAME=(0, 100), LAYER=1, MODE="PLAY")
		if self.timer >= 215 and self.timer <= 235:
			val = (self.timer-215)/20
			obj.color[0] = val
		if self.timer == 300:
			print("Chevron", id, "Locked")
			self.timer = 0
			self.chevron += 1

		self.timer += 1

		if len(self.data["ADDRESS"]) < self.chevron:
			self.ST_Active_Set()

	def ST_Active_Set(self):
		self.timer = 0
		self.active_state = self.ST_Active
		self.doEventHorizon("ON")

	def ST_Active(self):
		self.timer += 1

		player = self.doPuddle()

		if player != None:
			gd = logic.globalDict
			map = self.puddle.get("MAP", "")+".blend"
			door = self.objects["Root"].name
			if map in gd["BLENDS"]:
				player.doUpdate()
				#player.hideObject()
				lp, lr = player.getTransformDiff(self.puddle)
				#owner = self.puddle
				#root = player.objects["Root"]
				#WP = root.worldPosition
				#pnt = WP-owner.worldPosition
				#lp = owner.worldOrientation.inverted()*pnt
				#lp = list(lp)
				lp[1] *= -1
				#dr = owner.worldOrientation.to_euler()
				#pr = root.worldOrientation.to_euler()
				#lr = [pr[0]-dr[0], pr[1]-dr[1], pr[2]-dr[2]]
				gd["DATA"]["Portal"]["Zone"] = [lp, lr]
				gd["DATA"]["Portal"]["Door"] = door
				gd["DATA"]["Portal"]["Stargate"] = self.GALAXY
				base.settings.openWorldBlend(map)
				#gd["CURRENT"]["Level"] = map
				#blend = gd["DATA"]["GAMEPATH"]+"MAPS/"+map
				#logic.startGame(blend)
				self.puddle["MAP"] = ""

		if self.timer > 36000 or len(self.data["ADDRESS"]) == 0:
			self.ST_Shutdown_Set()

	def ST_Disabled_Set(self):
		self.data["ADDRESS"] = []
		self.timer = 0
		self.active_state = self.ST_Disabled
		self.doEventHorizon("END")


class CoreDHD(base.CoreObject):

	NAME = "Stargate DHD"
	GALAXY = "MILKYWAY"

	def ST_Startup(self):
		global ADDRESS

		if self.GALAXY not in base.LEVEL["STARGATE"]:
			base.LEVEL["STARGATE"][self.GALAXY] = {"Gate":None, "DHD":None}

		self.LOOKUP = ADDRESS[self.GALAXY]
		self.STARGATE = base.LEVEL["STARGATE"][self.GALAXY]

		self.STARGATE["DHD"] = self.objects["Root"]["DICT"]

		del self.objects["Root"]["RAYCAST"]
		del self.objects["Button"]["GROUND"]

		for key in self.objects["Keys"]:
			obj = self.objects["Keys"][key]
			obj["RAYCAST"] = None
			obj["RAYNAME"] = key
			obj.color = (0,0,0,1)

			del obj["GROUND"]

		self.objects["Button"]["RAYCAST"] = None
		self.objects["Button"]["RAYNAME"] = "Enter"
		self.objects["Button"].color = (0,0,0,1)

		self.data["ADDRESS"] = []

		self.timer = 0

	def doButton(self, key):
		obj = self.objects["Keys"][key]

		if key in self.data["ADDRESS"]:
			obj.color[0] = 1
			return

		chk = self.checkClicked(obj)
		if chk == True:
			self.timer = 0
			obj.color[0] = 1
			self.data["ADDRESS"].append(key)
		elif chk == False:
			obj.color[0] = 0.5
		else:
			obj.color[0] = 0

	def checkClicked(self, obj):
		if obj["RAYCAST"] != None:
			if keymap.BINDS["ACTIVATE"].tap() == True:
				return True
			return False
		return None

	def clearRayProps(self):
		for key in self.objects["Keys"]:
			obj = self.objects["Keys"][key]
			obj["RAYCAST"] = None
		self.objects["Button"]["RAYCAST"] = None

	## SHUTDOWN STATE ##
	def ST_Shutdown(self):
		self.timer -= 1

		if self.timer < 20:
			for key in self.objects["Keys"]:
				obj = self.objects["Keys"][key]
				obj.color[0] = obj.color[0]*(self.timer/20)

			self.objects["Button"].color[0] = (self.timer/20)

		if self.timer == 0:
			self.ST_Disabled_Set()

	def ST_Shutdown_Set(self):
		if self.STARGATE["Gate"] != None:
			self.STARGATE["Gate"]["Data"]["ADDRESS"] = []
		self.data["ADDRESS"] = []
		self.timer = 60
		self.active_state = self.ST_Shutdown

	## STATE DISABLED ##
	def ST_Disabled(self):
		button = self.objects["Button"]

		if self.timer > 0:
			self.timer -= 1
		if self.timer < 0:
			self.timer += 1

		for key in self.objects["Keys"]:
			self.doButton(key)

		enter = self.checkClicked(button)
		if enter == True:
			button.color[0] = 1
			self.ST_Active_Set()
		elif enter == False:
			button.color[0] = 0.5
		else:
			button.color[0] = 0

	def ST_Active_Set(self):
		print(self.data["ADDRESS"], len(self.data["ADDRESS"]))
		if len(self.data["ADDRESS"]) in [7, 8, 9]:
			if self.STARGATE["Gate"] != None:
				lookup = ":".join(self.data["ADDRESS"])
				if lookup in self.LOOKUP:
					self.STARGATE["Gate"]["Data"]["ADDRESS"] = self.data["ADDRESS"].copy()
					self.active_state = self.ST_Active
					return

		self.ST_Shutdown_Set()

	## STATE ACTIVE ##
	def ST_Active(self):
		if self.checkClicked(self.objects["Button"]) == True or len(self.data["ADDRESS"]) == 0:
			self.ST_Shutdown_Set()

	def ST_Disabled_Set(self):
		self.data["ADDRESS"] = []
		self.timer = 0
		self.active_state = self.ST_Disabled


class RedGate(CoreGate):

	NAME = "Milkyway Stargate"

	def doTrack(self, state):
		if state == "DIALING":
			self.objects["Track"].applyRotation((0, 0.01, 0), True)

	def ST_Iris(self):
		iris = self.objects["Iris"]
		state = self.data["IRIS"]

		if self.iris_state == "OPEN":
			if state == "CLOSE":
				self.iris_timer = 0
				self.iris_state = "CLOSING"

		elif self.iris_state == "CLOSED":
			if state == "OPEN":
				self.iris_timer = 0
				self.iris_state = "OPENING"

		elif self.iris_state == "OPENING":
			self.doAnim(OBJECT=iris, NAME="IrisKey", FRAME=(110,-10), KEY=True)
			self.iris_timer += 1
			if self.iris_timer == 15:
				self.setLights("ON")
			if self.iris_timer == 115:
				self.iris_timer = 0
				self.iris_state = "OPEN"

		elif self.iris_state == "CLOSING":
			self.doAnim(OBJECT=iris, NAME="IrisKey", FRAME=(0,120), KEY=True)
			self.iris_timer += 1
			if self.iris_timer == 60:
				self.setLights("OFF")
			if self.iris_timer == 115:
				self.iris_timer = 0
				self.iris_state = "CLOSED"

class RedDHD(CoreDHD):

	NAME = "Milkyway DHD"

class BlueGate(CoreGate):

	NAME = "Pegasus Stargate"
	GALAXY = "PEGASUS"

	def doTrack(self, state):
		if state == "OFF" or state == "START":
			self.objects["Track"].color[0] = 0
		if state == "ON" or state == "DIALING":
			self.objects["Track"].color[0] = 1

class BlueDHD(CoreDHD):

	NAME = "Pegasus DHD"
	GALAXY = "PEGASUS"


