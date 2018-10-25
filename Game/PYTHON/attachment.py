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

		self.SCALE = self.createVector(size=3, fill=self.SCALE)
		self.OFFSET = self.createVector(vec=self.OFFSET)
		for i in range(3):
			if self.SCALE[i] < 0.1:
				self.SCALE[i] = 0.1
			self.SCALE[i] = 1/self.SCALE[i]
			self.OFFSET[i] = self.OFFSET[i]*self.SCALE[i]

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

		#box.localScale = self.SCALE
		box["RAYCAST"] = None
		box["RAYNAME"] = self.NAME

		self.box = box
		self.box_timer = 1
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
		if offset == None:
			print("OFFSET NONE:", self.NAME)
		obj.localOrientation = self.createMatrix()
		if socket == self.box:
			obj.localPosition = self.OFFSET.copy()
			obj.worldScale = self.SCALE.copy()
		else:
			obj.localPosition = (0,0,0)
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

		self.box.worldPosition = self.data["POS"]

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
		offset = 1
		if self.box == None:
			box = self.objects["Root"]

		rayto = list(box.worldPosition)
		rayto[2] -= 1

		obj, pnt, nrm = box.rayCast(rayto, None, 10000, "", 1, 1, 0)

		if obj != None:
			box.worldPosition[2] = pnt[2]+(offset*0.5)
		else:
			obj, pnt, nrm = box.rayCast(rayto, None, 10000, "", 1, 1, 0)
			if obj != None:
				box.worldPosition[2] = pnt[2]+(offset*0.5)

	## STATE BOX ##
	def ST_Box(self):
		if self.box_timer == 0:
			self.checkStability(offset=self.SCALE[2])
		else:
			self.box_timer -= 1

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

	def RUN(self):
		if self.owning_player != None and self.box == None:
			if self.owning_player.objects["Root"] == None:
				return
		self.runPre()
		self.runStates()
		self.runPost()
		self.clearRayProps()
		self.stateSwitcher()

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



