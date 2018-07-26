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

## INVENTORY ITEMS ##


from bge import logic

import PYTHON.base as base
import PYTHON.keymap as keymap


class CoreAttachment(base.CoreObject):

	NAME = "Attachment"
	GHOST = True
	ENABLE = False
	SLOTS = []
	SCALE = 1.0
	OFFSET = (0,0,0)
	COLOR = (1,1,1,1)
	GFXBOX = {"Mesh":"GFX_Cube"}
	GFXDROP = {"Mesh":"GFX_Drop", "Halo":True}

	def __init__(self):
		owner = logic.getCurrentController().owner

		owner["Class"] = self

		owner["RAYCAST"] = owner.get("RAYCAST", None)
		owner["RAYNAME"] = self.NAME

		owner["DICT"]["Equiped"] = owner["DICT"].get("Equiped", None)

		self.objects = {"Root":owner}
		self.box = None

		self.owning_slot = None
		self.owning_player = None

		self.active_pre = []
		self.active_state = self.ST_Box
		self.active_post = []

		self.data = self.defaultData()
		self.data["HUD"] = {"Color":(1,1,1,1), "Stat":0, "Text":""}
		self.data["ENABLE"] = self.ENABLE
		self.data["COOLDOWN"] = 0

		self.SCALE = [self.SCALE, self.SCALE, self.SCALE]
		self.OFFSET = [self.OFFSET[0], self.OFFSET[1], self.OFFSET[2]]
		for i in range(3):
			if self.SCALE[i] < 0.1:
				self.SCALE[i] = 0.1
			self.OFFSET[i] = self.OFFSET[i]/self.SCALE[i]

		self.checkGhost(owner)
		self.findObjects(owner)
		self.doLoad()
		self.ST_Startup()

		if owner["DICT"]["Equiped"] not in [None, False, "DROP"]:
			self.equipItem(owner["RAYCAST"])
		else:
			self.dropItem()

	def saveWorldPos(self):
		obj = self.box
		if self.box == None:
			obj = self.objects["Root"]

		self.data["POS"] = self.vecTuple(obj.worldPosition)
		self.data["ORI"] = self.matTuple(obj.worldOrientation)

	def buildBox(self):
		owner = self.objects["Root"]

		if owner["DICT"]["Equiped"] == None:
			box = owner.scene.addObject(self.GFXBOX["Mesh"], owner, 0)
			box.color = self.COLOR
			owner["DICT"]["Equiped"] = None
		else:
			box = owner.scene.addObject(self.GFXDROP["Mesh"], owner, 0)
			if self.GFXDROP["Halo"] == True:
				halo = owner.scene.addObject("GFX_Halo", owner, 0)
				halo.setParent(box)
				#halo.color = self.COLOR
				halo["LOCAL"] = True
				halo["AXIS"] = None
			owner["DICT"]["Equiped"] = False

		box.localScale = self.SCALE
		box["RAYCAST"] = None
		box["RAYNAME"] = self.NAME

		self.box = box
		return box

	def assignToPlayer(self):
		owner = self.objects["Root"]
		slot = self.owning_slot
		cls = self.owning_player

		if owner["DICT"] not in cls.data["INVENTORY"]:
			cls.data["INVENTORY"].append(owner["DICT"])

		cls.data["INVSLOT"][slot] = owner["DICT"]

		cls.cls_dict[slot] = self

	def removeFromPlayer(self):
		owner = self.objects["Root"]
		slot = self.owning_slot
		cls = self.owning_player

		if cls == None:
			return

		if owner["DICT"] in cls.data["INVENTORY"]:
			cls.data["INVENTORY"].remove(owner["DICT"])

		if cls.data["INVSLOT"].get(slot, None) == owner["DICT"]:
			del cls.data["INVSLOT"][slot]

		if cls.cls_dict.get(slot, None) == self:
			del cls.cls_dict[slot]

	def attachToSocket(self, obj=None, socket=None, offset=(0,0,0)):
		if socket == None:
			return
		if obj == None:
			obj = self.objects["Root"]

		obj.setParent(socket)
		obj.localPosition = offset
		obj.localOrientation = self.createMatrix()
		obj.worldScale = (1,1,1)

	def equipItem(self, cls):
		owner = self.objects["Root"]
		slot = owner["DICT"]["Equiped"]

		for inv in self.SLOTS:
			if inv in cls.objects["INV"] and slot in [None, False, "DROP"]:
				if len(cls.objects["INV"][inv].children) == 0:
					slot = inv

		if slot in [None, False]:
			return

		obj = cls.objects["INV"][slot]

		if self.active_state == self.ST_Box:
			self.active_state = self.ST_Idle

		self.owning_slot = slot
		self.owning_player = cls

		self.assignToPlayer()
		self.attachToSocket(owner, obj)

		if self.box != None:
			self.box.endObject()
			self.box = None

		owner["DICT"]["Equiped"] = slot

		if self in logic.UPDATELIST:
			logic.UPDATELIST.remove(self)

	def dropItem(self):
		cls = self.owning_player
		owner = self.objects["Root"]

		owner.alignAxisToVect((0,0,1), 2, 1.0)

		self.buildBox()

		self.removeFromPlayer()
		self.attachToSocket(owner, self.box, self.OFFSET)

		self.box.worldPosition[0] = self.data["POS"][0]
		self.box.worldPosition[1] = self.data["POS"][1]
		self.box.worldPosition[2] = self.data["POS"][2]

		self.checkStability(offset=self.SCALE[2])

		self.active_state = self.ST_Box
		self.owning_slot = None
		self.owning_player = None

		if self not in logic.UPDATELIST and self.UPDATE == True:
			logic.UPDATELIST.append(self)

	def moveItem(self):
		owner = self.objects["Root"]
		slot = owner["DICT"]["Equiped"]
		cls = owning_player

		for inv in self.SLOTS:
			if inv in cls.objects["INV"]:
				if len(cls.objects["INV"][inv].children) == 0:
					slot = inv

		if slot in [None, False]:
			return

	def checkStability(self, align=False, offset=1.0):
		box = self.box
		if self.box == None:
			box = self.objects["Root"]

		rayto = list(box.worldPosition)
		rayto[2] -= 1

		obj, pnt, nrm = box.rayCast(rayto, None, 10000, "", 1, 1, 0)

		if obj != None:
			box.worldPosition[2] = pnt[2]+(offset*0.375)
		else:
			obj, pnt, nrm = box.rayCast(rayto, None, 10000, "", 1, 1, 0)
			if obj != None:
				box.worldPosition[2] = pnt[2]+(offset*0.375)

	## STATE BOX ##
	def ST_Box(self):
		self.checkStability(offset=self.SCALE[2])

		if self.checkClicked(self.box) == True:
			self.equipItem(self.box["RAYCAST"])

	## STATE TRIGGER ##
	def ST_Enable(self):
		pass

	def ST_Stop(self):
		pass

	## STATE IDLE ##
	def ST_Idle(self):
		pass

	def stateSwitcher(self):
		owner = self.objects["Root"]
		state = owner["DICT"]["Equiped"]

		if state == "DROP":
			self.ST_Stop()
			self.dropItem()

	def clearRayProps(self):
		owner = self.objects["Root"]

		if self.box != None:
			self.box["RAYCAST"] = None

		self.stateSwitcher()


class JetPack(CoreAttachment):

	NAME = "JetPack"
	SLOTS = ["Back"]
	OFFSET = (0, 0, 0)
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


class Firefly(CoreAttachment):

	NAME = "Firefly JetPack"
	SLOTS = ["Back"]
	ENABLE = False
	OFFSET = (0, -0.05, 0.1)
	SCALE = 1.6
	POWER = 10
	FUEL = 100000

	def defaultData(self):
		self.power = self.createVector(3)
		self.animframe = [10, 10]
		dict = {"FUEL":self.FUEL}
		return dict

	def ST_Startup(self):
		self.doEffects("INIT")

	def ST_Enable(self):
		if self.owning_player.jump_state == "NONE":
			self.owning_player.doJump()
		self.owning_player.jump_state = "JETPACK"
		self.active_state = self.ST_Active

	def ST_Stop(self):
		self.doEffects("STOP")
		self.owning_player.doAnim(STOP=True)

		if self.owning_player.jump_state == "JETPACK":
			self.owning_player.jump_state = "FALLING"

		self.active_state = self.ST_Idle

	def ST_Idle(self):
		plr = self.owning_player

		if plr.jump_state == "FLYING":
			self.data["ENABLE"] = False

		if self.data["ENABLE"] == True:
			self.ST_Enable()

	def ST_Active(self):
		plr = self.owning_player

		if plr.jump_state in ["NONE", "FLYING"]:
			self.data["ENABLE"] = False

		if self.data["ENABLE"] == False:
			self.ST_Stop()
			return

		self.power[0] = 0
		self.power[1] = 0
		self.power[2] = 0

		if self.data["FUEL"] > 0:
			self.power[2] = 1

			mx = 1+(plr.motion["Climb"]*0.3)
			burn = 1

			if plr.motion["Climb"] > 0.5:
				burn = 2
			elif plr.motion["Climb"] < -0.5:
				burn = 0

			if plr.motion["Move"].length > 0.01:
				move = plr.motion["Move"].normalized()
				#mref = plr.objects["VertRef"].getAxisVect((move[0], move[1], 0))
				self.power[0] = move[0]*0.5
				self.power[1] = move[1]*0.5

				if plr.motion["Move"].length > 0.1:
					plr.alignPlayer(factor=0.05)

				self.power.normalize()

			plr.objects["Root"].applyForce(self.power*self.POWER*mx, True)
			self.data["FUEL"] -= burn

		else:
			self.data["ENABLE"] = False

		plr.doAnim(NAME="Flying", FRAME=(10,10), MODE="LOOP", BLEND=10)
		self.doEffects("ACTIVE")

	def doEffects(self, state=None):
		self.data["HUD"]["Stat"] = round((self.data["FUEL"]/self.FUEL)*100, 1)
		self.data["HUD"]["Text"] = str(self.data["HUD"]["Stat"])

		plr = self.owning_player

		if state in ["INIT", "STOP"]:
			self.ANIMOBJ = self.objects["Rig"]
			self.doAnim(STOP=True)
			self.doAnim(NAME="INV_Firefly.Rest", FRAME=(0,0), MODE="LOOP", BLEND=10)
			self.objects["Fire_L"].localScale = (1,1,0)
			self.objects["Fire_R"].localScale = (1,1,0)
			return

		elif state == "ACTIVE":
			mx = 10+(plr.motion["Move"][1]*10)

			self.animframe[1] += (mx-self.animframe[1])*0.1

			self.doAnim(NAME="INV_Firefly.Y", FRAME=(-5,25), MODE="LOOP", BLEND=10)
			self.doAnim(SET=self.animframe[1])

			fire = 1+(plr.motion["Climb"]*0.5)

			self.objects["Fire_L"].localScale = (1,1,fire)
			self.objects["Fire_R"].localScale = (1,1,fire)


