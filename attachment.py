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

from . import base, keymap


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

		self.defaultStates()

		self.dict = owner["DICT"]
		self.data = self.defaultData()

		self.data["HUD"] = {"Color":(1,1,1,1), "Stat":100, "Text":""}
		self.data["ENABLE"] = None #self.ENABLE
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
			self.equipItem(owner["RAYCAST"], load=True)
		else:
			self.dropItem(load=True)

	def defaultStates(self):
		self.active_pre = []
		self.active_state = self.ST_Box
		self.active_post = []

	def saveWorldPos(self):
		obj = self.box
		if self.box == None:
			obj = self.objects["Root"]

		self.data["POS"] = self.vecTuple(obj.worldPosition)
		self.data["ORI"] = self.matTuple(obj.worldOrientation)

	def buildBox(self):
		owner = self.objects["Root"]

		if self.dict["Equiped"] == None:
			box = owner.scene.addObject(self.GFXBOX["Mesh"], owner, 0)
			box.color = self.COLOR
			self.dict["Equiped"] = None
		else:
			box = owner.scene.addObject(self.GFXDROP["Mesh"], owner, 0)
			if self.GFXDROP["Halo"] == True:
				halo = owner.scene.addObject("GFX_Halo", owner, 0)
				halo.setParent(box)
				#halo.color = self.COLOR
				halo["LOCAL"] = True
				halo["AXIS"] = None
			self.dict["Equiped"] = False

		#box.localScale = self.SCALE
		box["RAYCAST"] = None
		box["RAYNAME"] = self.NAME

		self.box = box
		self.box_timer = 1
		return box

	def assignToPlayer(self):
		slot = self.owning_slot
		cls = self.owning_player

		if self.dict not in cls.data["INVENTORY"]:
			cls.data["INVENTORY"].append(self.dict)

		cls.data["INVSLOT"][slot] = self.dict

		cls.cls_dict[slot] = self

	def removeFromPlayer(self):
		slot = self.owning_slot
		cls = self.owning_player

		if cls == None:
			return

		if self.dict in cls.data["INVENTORY"]:
			cls.data["INVENTORY"].remove(self.dict)

		if cls.data["INVSLOT"].get(slot, None) == self.dict:
			del cls.data["INVSLOT"][slot]

		if cls.cls_dict.get(slot, None) == self:
			del cls.cls_dict[slot]

	def attachToSocket(self, obj=None, socket=None):
		if socket == None:
			return
		if obj == None:
			obj = self.objects["Root"]

		obj.setParent(socket)
		obj.localOrientation = self.createMatrix()

		if socket == self.box:
			obj.localPosition = self.OFFSET.copy()
			obj.worldScale = self.SCALE.copy()
		else:
			obj.localPosition = (0,0,0)
			obj.worldScale = (1,1,1)

	def equipItem(self, cls, load=False):
		owner = self.objects["Root"]
		slot = self.dict["Equiped"]

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

		self.dict["Equiped"] = slot

		if self in logic.UPDATELIST:
			logic.UPDATELIST.remove(self)

		if self.data["ENABLE"] == None:
			if self.ENABLE == True:
				self.stateSwitch(True, run=True, force=True)
			else:
				self.data["ENABLE"] = False

	def dropItem(self, pos=None, load=False):
		cls = self.owning_player
		owner = self.objects["Root"]

		if load == False:
			self.dict["Equiped"] = "DROP"
			self.ST_Stop()

		owner.alignAxisToVect((0,0,1), 2, 1.0)

		self.buildBox()

		self.removeFromPlayer()
		self.attachToSocket(owner, self.box)

		if pos != None:
			self.data["POS"] = list(pos)
		self.box.worldPosition = self.data["POS"]

		self.active_state = self.ST_Box
		self.owning_slot = None
		self.owning_player = None

		if self not in logic.UPDATELIST and self.UPDATE == True:
			logic.UPDATELIST.append(self)

	def moveItem(self):
		owner = self.objects["Root"]
		slot = self.dict["Equiped"]
		cls = owning_player

		for inv in self.SLOTS:
			if inv in cls.objects["INV"]:
				if len(cls.objects["INV"][inv].children) == 0:
					slot = inv

		if slot in [None, False]:
			return

	def checkStability(self, align=False, offset=None):
		box = self.box
		if self.box == None:
			box = self.objects["Root"]
		if offset == None:
			offset = box.worldScale[2]

		rayto = list(box.worldPosition)
		rayto[2] -= 1

		obj, pnt, nrm = box.rayCast(rayto, None, 10000, "", 1, 1, 0)

		if obj != None:
			box.worldPosition[2] = pnt[2]+(offset*0.5)
		else:
			obj, pnt, nrm = box.rayCast(rayto, None, 10000, "", 1, 1, 0)
			if obj != None:
				box.worldPosition[2] = pnt[2]+(offset*0.5)

	def stateSwitch(self, state=None, run=False, force=False):
		if state == None:
			if self.data["ENABLE"] == True:
				state = False
			else:
				state = True
		elif state != True:
			state = False

		if force == False:
			if self.box != None or self.data["COOLDOWN"] != 0 or self.data["ENABLE"] == state:
				return False

		if state == True:
			self.active_state = self.ST_Enable
		else:
			self.active_state = self.ST_Stop
		self.data["ENABLE"] = state

		if run == True:
			self.active_state()

		return True

	## STATE BOX ##
	def ST_Box(self):
		if self.box_timer == 0:
			self.checkStability()
		else:
			self.box_timer -= 1

		if self.checkClicked(self.box) == True:
			self.equipItem(self.box["RAYCAST"])

	## STATE TRIGGER ##
	def ST_Enable(self):
		self.active_state = self.ST_Active

	def ST_Stop(self):
		self.active_state = self.ST_Idle

	## STATES ##
	def ST_Idle(self):
		pass

	def ST_Active(self):
		pass

	def RUN(self):
		if self.owning_player != None and self.box == None:
			if self.owning_player.objects["Root"] == None:
				return
		self.runPre()
		self.runStates()
		self.runPost()
		self.clearRayProps()

	def clearRayProps(self):
		if self.box != None:
			self.box["RAYCAST"] = None



