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

## WEAPON CORE ##


from bge import logic

from . import attachment, keymap


class CoreWeapon(attachment.CoreAttachment):

	NAME = "Weapon"
	ENABLE = False
	SLOTS = []
	COLOR = (0,1,0,1)
	TYPE = "RANGED"
	HAND = "MAIN"
	WAIT = 40

	def defaultStates(self):
		self.active_pre = []
		self.active_state = self.ST_Box
		self.active_post = []

	def assignToPlayer(self):
		slot = self.owning_slot
		cls = self.owning_player

		if self.dict not in cls.data["WEAPONS"]:
			cls.data["WEAPONS"].append(self.dict)

		cls.data["INVSLOT"][slot] = self.dict

		if slot not in cls.data["WPDATA"]["WHEEL"][self.TYPE]["LIST"]:
			cls.data["WPDATA"]["WHEEL"][self.TYPE]["LIST"].append(slot)

		cls.cls_dict[slot] = self

		if self.data["ENABLE"] == True:
			cls.active_weapon = self
			hand = cls.objects["SKT"][cls.HAND[self.HAND]]
			self.attachToSocket(self.objects["Mesh"], hand)
			self.doPlayerAnim("LOOP")

	def removeFromPlayer(self):
		slot = self.owning_slot
		cls = self.owning_player

		if cls == None:
			return

		if self.dict in cls.data["WEAPONS"]:
			cls.data["WEAPONS"].remove(self.dict)

		if cls.data["INVSLOT"].get(slot, None) == self.dict:
			del cls.data["INVSLOT"][slot]

		weap = cls.data["WPDATA"]["WHEEL"][self.TYPE]

		if slot in weap["LIST"]:
			weap["LIST"].remove(slot)

		if weap["ID"] >= len(weap["LIST"]):
			weap["ID"] = len(weap["LIST"])-1
		if weap["ID"] == -1:
			cls.data["WPDATA"]["CURRENT"] = "NONE"

		if cls.cls_dict.get(slot, None) == self:
			del cls.cls_dict[slot]

	def doPlayerAnim(self, frame=0):
		plr = self.owning_player
		anim = self.TYPE+plr.HAND[self.HAND]+self.owning_slot
		start = 0
		end = 40
		lyr = 1+(self.HAND=="OFF")

		if frame == "LOOP":
			plr.doAnim(NAME=anim, FRAME=(end,end), LAYER=lyr, PRIORITY=2, MODE="LOOP")
		elif frame == "STOP":
			plr.doAnim(LAYER=lyr, STOP=True)
		elif type(frame) is int:
			plr.doAnim(NAME=anim, FRAME=(start,end), LAYER=lyr)
			fac = (frame/self.WAIT)
			if frame < 0:
				fac = 1+fac
			plr.doAnim(LAYER=lyr, SET=fac*end)

	def getEffectValue(self):
		scale = -1

		if self.active_state in [self.ST_Stop, self.ST_Enable]:
			fac = (self.data["COOLDOWN"]/self.WAIT)
			if fac < 0:
				fac = 1+fac

			scale = (fac*2)-1

		return scale

	def ST_Startup(self):
		self.data["HUD"]["Stat"] = 100
		self.data["HUD"]["Text"] = ""

	## STATE TRANSITION ##
	def ST_Enable(self):
		if self.data["COOLDOWN"] == int(self.WAIT*0.5):
			hand = self.owning_player.HAND[self.HAND]
			hand = self.owning_player.objects["SKT"][hand]
			self.attachToSocket(self.objects["Mesh"], hand)

		self.data["COOLDOWN"] += 1
		self.doPlayerAnim(self.data["COOLDOWN"])

		if self.data["COOLDOWN"] == self.WAIT:
			self.doPlayerAnim("LOOP")
			self.data["COOLDOWN"] = 0
			self.active_state = self.ST_Active

	def ST_Stop(self):
		self.data["COOLDOWN"] -= 1
		self.doPlayerAnim(self.data["COOLDOWN"])

		if self.data["COOLDOWN"] == int(-self.WAIT*0.5) or self.dict["Equiped"] == "DROP":
			self.attachToSocket(self.objects["Mesh"], self.objects["Socket"])

		if self.data["COOLDOWN"] == -self.WAIT or self.dict["Equiped"] == "DROP":
			self.doPlayerAnim("STOP")
			self.owning_player.active_weapon = None
			self.data["COOLDOWN"] = 0
			self.data["ENABLE"] = False
			self.active_state = self.ST_Idle



