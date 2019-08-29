####
# bge_game3_core: Full python game structure for the Blender Game Engine
# Copyright (C) 2019  DaedalusMDW @github.com (Daedalus_MDW @blenderartists.org)
# https://github.com/DaedalusMDW/bge_game3_core
#
# This file is part of bge_game3_core.
#
#    bge_game3_core is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    bge_game3_core is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with bge_game3_core.  If not, see <http://www.gnu.org/licenses/>.
#
####

## POWERUPS ##


from bge import logic

from . import attachment, keymap


class CorePowerup(attachment.CoreAttachment):

	NAME = "PowerUp"
	WAIT = 3600
	DURATION = 0
	COLLIDE = True
	OFFSET = (0,0,0)
	GFXBOX = {"Mesh":"BOX_Sphere", "Halo":True}
	GFXDROP = {"Mesh":"BOX_Sphere", "Halo":True}

	def checkData(self, cls):
		return True

	def sendPowerup(self):
		return {}

	def equipItem(self, cls):
		if "POWERUPS" not in cls.data:
			return
		if self.checkData(cls) == False:
			return

		dict = self.sendPowerup()
		dict["__TIMER__"] = self.DURATION
		cls.data["POWERUPS"].append(dict)

		self.data["COOLDOWN"] = self.WAIT
		self.hideObject(True)

		self.active_state = self.ST_Wait

	## STATE INACTIVE ##
	def ST_Wait(self):
		if self.data["COOLDOWN"] < 0:
			if self in logic.UPDATELIST:
				logic.UPDATELIST.remove(self)

			self.box.endObject()
			self.box = None
			return

		if self.data["COOLDOWN"] == 0:
			self.data["COOLDOWN"] = 0
			self.hideObject(False)
			self.campers = list(self.box["COLLIDE"])
			self.box["RAYNAME"] = self.NAME
			self.active_state = self.ST_Box
		else:
			self.data["COOLDOWN"] -= 1
			self.box["RAYNAME"] = self.NAME+": "+str(int(self.data["COOLDOWN"]))

	## STATE BOX ##
	def ST_Box(self):
		if self.data["COOLDOWN"] != 0:
			self.hideObject(True)
			self.active_state = self.ST_Wait
			return

		for plr in self.campers:
			if plr not in self.box["COLLIDE"]:
				self.campers.remove(plr)

		if self.checkClicked(self.box) == True:
			if self.box["RAYCAST"] not in self.campers:
				self.equipItem(self.box["RAYCAST"])


class CoreStats(CorePowerup):

	HEALTH = 0
	ENERGY = 0
	LIMIT = 99

	def checkData(self, cls):
		if self.HEALTH != 0 and cls.data.get("HEALTH", 100) < self.LIMIT:
			return True
		if self.ENERGY != 0 and cls.data.get("ENERGY", 100) < self.LIMIT:
			return True

		return False

	def sendPowerup(self):
		return {"HEALTH":self.HEALTH, "ENERGY":self.ENERGY}


class CoreKey(CorePowerup):

	LOCK = 1
	WAIT = -1
	COLLIDE = False
	GFXBOX = {"Mesh":"BOX_Sphere", "Halo":False}
	GFXDROP = {"Mesh":"BOX_Sphere", "Halo":False}

	def defaultData(self):
		LOCK = self.objects["Root"].get("LOCK", self.LOCK)

		dict = {"LOCK":LOCK}
		return dict

	def ST_Startup(self):
		self.objects["Root"]["RAYNAME"] = "Key: "+str(self.data["LOCK"])

	def sendPowerup(self):
		return {"KEYRING": self.data["LOCK"]}


