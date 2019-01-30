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
	GFXBOX = {"Mesh":"BOX_Sphere"}
	GFXDROP = {"Mesh":"BOX_Sphere", "Halo":False}

	## STATE BOX ##
	def ST_Box(self):
		if self.checkClicked(self.box) == True:
			self.equipItem(self.box["RAYCAST"])


class CoreKey(CorePowerup):

	OFFSET = (0,0,0)
	LOCK = 1

	def defaultData(self):
		LOCK = self.objects["Root"].get("LOCK", self.LOCK)

		dict = {"LOCK":LOCK}
		return dict

	def ST_Startup(self):
		self.objects["Root"]["RAYNAME"] = "Key: "+str(self.data["LOCK"])

	def equipItem(self, cls):
		cls.data["KEYRING"].append(self.data["LOCK"])

		if self in logic.UPDATELIST:
			logic.UPDATELIST.remove(self)

		self.box.endObject()
		self.box = None

