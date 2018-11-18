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

## POWERUPS ##


from bge import logic

from . import attachment, keymap


class CorePowerup(attachment.CoreAttachment):

	NAME = "PowerUp"
	SCALE = (1,1,1)
	OFFSET = (0,0,0)
	GFXBOX = {"Mesh":"GFX_PowerUp"}
	GFXDROP = {"Mesh":"GFX_PowerUp", "Halo":False}

	def __init__(self):
		owner = logic.getCurrentController().owner

		owner["Class"] = self

		owner["RAYCAST"] = owner.get("RAYCAST", None)
		owner["RAYNAME"] = self.NAME

		owner["DICT"]["Equiped"] = False

		self.objects = {"Root":owner}
		self.box = None

		self.owning_player = None

		self.active_pre = []
		self.active_state = self.ST_Box
		self.active_post = []

		self.data = self.defaultData()

		self.SCALE = [self.SCALE[0], self.SCALE[1], self.SCALE[2]]
		self.OFFSET = [self.OFFSET[0], self.OFFSET[1], self.OFFSET[2]]
		for i in range(3):
			if self.SCALE[i] < 0.1:
				self.SCALE[i] = 0.1
			self.OFFSET[i] = self.OFFSET[i]/self.SCALE[i]

		self.checkGhost(owner)
		self.findObjects(owner)
		self.doLoad()

		self.active_state = self.ST_Box

		self.buildBox()
		self.attachToSocket(owner, self.box)

		self.ST_Startup()

	def attachToSocket(self, obj=None, socket=None):
		if socket == None:
			return
		if obj == None:
			obj = self.objects["Root"]

		obj.setParent(socket)
		obj.localOrientation = self.createMatrix()

		if socket == self.box:
			self.box.localScale = self.SCALE
			obj.localPosition = self.OFFSET
			obj.localScale = [1/self.SCALE[0], 1/self.SCALE[1], 1/self.SCALE[2]]
		else:
			obj.localPosition = (0,0,0)
			obj.worldScale = (1,1,1)

	## STATE BOX ##
	def ST_Box(self):
		if self.checkClicked(self.box) == True:
			self.equipItem(self.box["RAYCAST"])


class SimpleKey(CorePowerup):

	SCALE = (0.1, 0.2, 0.05)
	OFFSET = (0,0,0)
	LOCK = 1

	def defaultData(self):
		LOCK = self.objects["Root"].get("LOCK", self.LOCK)

		dict = {"LOCK":LOCK}
		return dict

	def ST_Startup(self):
		self.box["RAYNAME"] = "Key: "+str(self.data["LOCK"])

	def equipItem(self, cls):
		cls.data["KEYRING"].append(self.data["LOCK"])

		if self in logic.UPDATELIST:
			logic.UPDATELIST.remove(self)

		self.box.endObject()
		self.box = None

