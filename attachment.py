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
	SCALE = 1
	OFFSET = (0,0,0)
	COLOR = (1,1,1,1)
	COLLIDE = False
	GFXBOX = {"Mesh":"BOX_Cube", "Normalize":True}
	GFXDROP = {"Mesh":"BOX_Drop", "Halo":True, "Normalize":True}

	def __init__(self):
		owner = logic.getCurrentController().owner

		owner["Class"] = self

		owner["RAYCAST"] = owner.get("RAYCAST", None)
		owner["RAYNAME"] = self.NAME

		owner["DICT"]["Equiped"] = owner["DICT"].get("Equiped", None)

		self.objects = {"Root":owner}
		self.box = None
		self.halo = None
		self.campers = []

		self.owning_slot = None
		self.owning_player = None

		self.defaultStates()

		self.dict = owner["DICT"]
		self.data = self.defaultData()

		self.data["HUD"] = {"Color":(1,1,1,1), "Stat":100, "Text":""}
		self.data["ENABLE"] = None #self.ENABLE
		self.data["COOLDOWN"] = 0

		self.box_scale = self.createVector(fill=self.SCALE)
		self.gfx_scale = self.createVector(fill=self.SCALE)

		self.checkGhost(owner)
		self.applyGravity()
		self.findObjects(owner)
		self.doLoad()
		self.ST_Startup()

		if owner["DICT"]["Equiped"] not in [None, False, "DROP"]:
			self.equipItem(owner["RAYCAST"], load=True)
		else:
			self.dropItem(load=True)

		del owner["RAYCAST"]

	def defaultStates(self):
		self.active_pre = [self.PR_Modifiers]
		self.active_state = self.ST_Box
		self.active_post = []

	def saveWorldPos(self):
		obj = self.box
		if self.box == None:
			obj = self.objects["Root"]

		self.data["POS"] = self.vecTuple(obj.worldPosition)
		self.data["ORI"] = self.matTuple(obj.worldOrientation)

	def getSocketScale(self):
		scale = self.createVector(size=3, fill=1.0)
		scale[0] *= (1/self.box_scale[0])
		scale[1] *= (1/self.box_scale[1])
		scale[2] *= (1/self.box_scale[2])
		return scale

	def getSocketPos(self):
		pos = self.createVector(vec=self.OFFSET)
		pos[0] *= (1/self.box_scale[0])
		pos[1] *= (1/self.box_scale[1])
		pos[2] *= (1/self.box_scale[2])
		return pos

	def hideObject(self, state=True):
		owner = self.objects["Root"]
		state = (state==False)
		owner.setVisible(state, True)
		#if self.halo != None:
		#	self.halo.setVisible(state, True)

	def buildBox(self):
		owner = self.objects["Root"]

		if self.dict["Equiped"] == None:
			gfx = self.GFXBOX
			self.dict["Equiped"] = None
			halo_color = self.COLOR
		else:
			gfx = self.GFXDROP
			self.dict["Equiped"] = False
			halo_color = (1,1,1,1)

		self.box_scale = self.createVector(vec=gfx.get("Scale", (1,1,1)))*self.SCALE
		self.gfx_scale = self.createVector(fill=self.SCALE)

		if gfx.get("Normalize", False) == True:
			scale = self.createVector(fill=1.0)
			gfxsc = scale.copy()
		else:
			scale = self.box_scale
			gfxsc = self.gfx_scale

		box = owner.scene.addObject(gfx.get("Mesh", "BOX_Drop"), owner, 0)
		box.worldScale = scale
		box.color = self.COLOR
		self.box = box
		self.box_timer = 1

		if gfx.get("Halo", False) == True:
			halo = owner.scene.addObject("GFX_Halo", owner, 0)
			halo.setParent(box)
			halo.color = halo_color
			halo.worldScale = gfxsc
			halo["LOCAL"] = True
			halo["AXIS"] = None
			self.halo = halo

		box["RAYCAST"] = None
		box["RAYNAME"] = owner["RAYNAME"]

		box["COLLIDE"] = []

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
			obj.localPosition = self.getSocketPos()
			obj.localScale = self.getSocketScale()
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
		self.halo = None

		self.dict["Equiped"] = slot

		if self in logic.UPDATELIST:
			logic.UPDATELIST.remove(self)

		if self.data["ENABLE"] == None:
			if self.ENABLE == True:
				self.stateSwitch(True, run=True, force=True)
			else:
				self.data["ENABLE"] = False
		elif self.data["ENABLE"] == True and load == False:
			self.stateSwitch(True, run=True, force=True)

	def dropItem(self, pos=None, load=False):
		cls = self.owning_player
		owner = self.objects["Root"]

		if load == False:
			self.dict["Equiped"] = "DROP"
			self.ST_Stop()

			self.gravity = cls.gravity.copy()

		self.buildBox()

		self.removeFromPlayer()
		self.hideObject(False)
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

	def checkClicked(self, obj=None):
		if obj == None:
			obj = self.objects["Root"]

		if self.COLLIDE == True:
			if len(obj["COLLIDE"]) >= 1:
				obj["RAYCAST"] = obj["COLLIDE"][0]
				return True

		if obj["RAYCAST"] != None:
			if keymap.BINDS["ACTIVATE"].tap() == True:
				return True
		return False

	def checkStability(self, align=False, offset=None):
		box = self.box
		if self.box == None:
			box = self.objects["Root"]
		if offset == None:
			offset = box.worldScale[2]

		rayto = box.worldPosition.copy()
		if self.gravity.length >= 0.1:
			rayto += self.gravity.normalized()
		else:
			rayto += box.getAxisVect((0,0,-1))

		obj, pnt, nrm = box.rayCast(rayto, None, 10000, "", 1, 1, 0)

		if obj != None:
			box.worldPosition = pnt+box.getAxisVect((0,0,offset*0.5))
		else:
			obj, pnt, nrm = box.rayCast(rayto, None, -10000, "", 1, 1, 0)
			if obj != None:
				box.worldPosition = pnt+box.getAxisVect((0,0,offset*0.5))

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

	def PR_Modifiers(self):
		if self.owning_player == None:
			return

	## STATE BOX ##
	def ST_Box(self):
		self.alignToGravity(self.box)

		if self.box_timer == 0:
			self.checkStability()
		else:
			self.box_timer -= 1
		if self.checkClicked(self.box) == True:
			self.equipItem(self.box["RAYCAST"])

		#self.clearRayProps()

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
		#if self.owning_player != None and self.box == None:
		#	if self.owning_player.objects["Root"] == None:
		#		return
		#if self.box != None:
		#	self.ST_Box()
		#	return
		self.runPre()
		self.runStates()
		self.runPost()
		self.clearRayProps()

	def clearRayProps(self):
		self.objects["Root"]["COOLDOWN"] = self.data["COOLDOWN"]
		self.objects["Root"].addDebugProperty("COOLDOWN", True)
		if self.box != None:
			self.box["RAYCAST"] = None
			self.box["COLLIDE"] = []



